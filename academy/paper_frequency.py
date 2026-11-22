"""Use Gemini to classify actual past-paper questions and count distinct papers locally."""
from collections import defaultdict
import json
import re
import unicodedata

from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .access import role_required, subjects_for
from .models import DocumentChunk
from .study_tools import StudyToolError, ai_available, generate, indexed_resources

PAPER_LIMIT = 6
CORPUS_LIMIT = 36_000


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def grouping_key(text):
    return ' '.join(re.findall(r'\w+', normalized(text)))


class PaperFrequencyForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = subjects_for(user)


def paper_corpus(user, subject):
    resources = indexed_resources(user).filter(subject=subject, kind='pyp').order_by('-created_at', '-pk')
    papers = []
    seen = set()
    remaining = CORPUS_LIMIT
    passages = {}
    # Inspect a bounded list and give priority to recently uploaded papers.
    for paper in resources[:30]:
        pages = defaultdict(list)
        size = 0
        for page, text in DocumentChunk.objects.filter(resource=paper).order_by('page', 'position').values_list('page', 'text').iterator():
            previous = pages[page][-1].split() if pages[page] else []
            words = text.split()
            overlap = min(60, len(previous), len(words))
            while overlap and previous[-overlap:] != words[:overlap]:
                overlap -= 1
            rest = ' '.join(words[overlap:])
            if rest:
                pages[page].append(rest)
                size += len(rest) + 1
            if size > remaining:
                break
        if not size or size > remaining:
            continue
        page_text = {page: ' '.join(parts) for page, parts in pages.items() if parts}
        fingerprint = normalized(' '.join(page_text.values()))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        remaining -= size
        papers.append(paper)
        for page, text in page_text.items():
            passages[(paper.pk, page)] = (paper, text, normalized(text))
        if len(papers) == PAPER_LIMIT:
            break
    return papers, passages, resources.count()


def counted_rows(payload, passages):
    """Ignore claims without a matching verbatim question on the selected page."""
    if not isinstance(payload, list):
        raise ValueError('Expected a list of observed questions.')
    topics, questions = {}, {}
    observed = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        paper_id, page = item.get('paper'), item.get('page')
        if type(paper_id) is not int or type(page) is not int:
            continue
        passage = passages.get((paper_id, page))
        quote, topic, task = item.get('quote'), item.get('topic'), item.get('question')
        if not passage or any(
            not isinstance(value, str) or not low <= len(value.strip()) <= high
            for value, low, high in ((quote, 12, 900), (topic, 3, 120), (task, 8, 220))
        ):
            continue
        evidence = normalized(quote)
        if not re.search(r'(?<!\w)' + re.escape(evidence) + r'(?!\w)', passage[2]):
            continue
        evidence_key = (paper_id, grouping_key(quote))
        if evidence_key in observed:
            continue
        observed.add(evidence_key)
        source = {'paper': passage[0], 'page': page, 'quote': quote.strip()}
        for groups, label in ((topics, topic), (questions, task)):
            key = grouping_key(label)
            if not key:
                continue
            row = groups.setdefault(key, {'label': label.strip(), 'sources': {}})
            row['sources'].setdefault(paper_id, source)

    def ranked(groups, minimum=1):
        rows = [
            {'label': row['label'], 'count': len(row['sources']), 'sources': list(row['sources'].values())}
            for row in groups.values() if len(row['sources']) >= minimum
        ]
        return sorted(rows, key=lambda row: (-row['count'], row['label'].casefold()))

    return ranked(topics), ranked(questions, minimum=2)


@role_required()
@require_http_methods(['GET', 'POST'])
@never_cache
def paper_frequency(request):
    if request.user.is_superuser:
        raise PermissionDenied
    form = PaperFrequencyForm(request.POST if request.method == 'POST' else None,
                              user=request.user, initial={'subject': request.GET.get('subject')})
    result = None
    if request.method == 'POST' and form.is_valid():
        subject = form.cleaned_data['subject']
        papers, passages, eligible_count = paper_corpus(request.user, subject)
        if not papers:
            form.add_error(None, 'No approved, indexed past paper fits the analysis limit. Ask your administrator to index the paper or split a long collection into individual exams.')
        elif ai_available(form, request):
            instructions = (
                'Extract actual assessable questions or subquestions from the supplied previous-year exam papers. '
                'Ignore headers, instructions, marks, answer keys and reference text. Review all papers together. '
                'For each question return an object with paper (integer), page (integer), quote (complete verbatim '
                'question or subquestion from that page), topic (short canonical concept), and question (canonical '
                'wording of the specific task). Reuse exactly the same topic label across wording variants. Reuse '
                'exactly the same question label only for tasks that ask students to do substantively the same thing. '
                'Keep different tasks about the same topic separate. Include one primary topic per item. Skip unclear '
                'or truncated questions. Return only a JSON array. Never calculate counts or predict future exams.'
            )
            corpus = '\n\n'.join(
                f'[Paper {paper_id}, page/section {page}]\n{text}'
                for (paper_id, page), (_, text, _) in passages.items()
            )
            try:
                payload = generate(instructions, f'Subject: {subject.name}\n\n{corpus}',
                                   structured=True, output_tokens=16_384)
                topics, questions = counted_rows(json.loads(payload), passages)
            except StudyToolError as exc:
                form.add_error(None, str(exc))
            except ValueError:
                form.add_error(None, 'Clarity could not complete the paper analysis. Try again shortly.')
            else:
                verified = {source['paper'].pk for row in topics for source in row['sources']}
                result = {
                    'subject': subject, 'papers': papers, 'eligible_count': eligible_count,
                    'topics': topics, 'questions': questions, 'verified_count': len(verified),
                    'unverified_papers': [paper for paper in papers if paper.pk not in verified],
                }
    return render(request, 'academy/paper_frequency.html', {'form': form, 'result': result})
