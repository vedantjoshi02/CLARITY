"""Read private resources in the browser using the existing resource access rules."""
import base64
import logging

from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_safe
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from .access import resources_for, role_required
from .engagement import track_resource

logger = logging.getLogger(__name__)
RASTER_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp'}


class OfficePreview:
    def __init__(self):
        self.image_budget = 5 * 1024 * 1024
        self.images_omitted = False

    def picture(self, mime, blob):
        if mime not in RASTER_TYPES or len(blob) > self.image_budget:
            self.images_omitted = True
            return None
        self.image_budget -= len(blob)
        data = base64.b64encode(blob).decode('ascii')
        return {'image': f'data:{mime};base64,{data}'}

    def word_blocks(self, document):
        for element in document.element.body:
            if element.tag == qn('w:tbl'):
                table = Table(element, document)
                yield {'table': [[cell.text for cell in row.cells] for row in table.rows]}
            elif element.tag == qn('w:p'):
                paragraph = Paragraph(element, document)
                if paragraph.text.strip():
                    level = paragraph.style.name if paragraph.style else ''
                    yield {'text': paragraph.text, 'heading': level.startswith(('Heading', 'Title'))}
                for blip in element.xpath('.//a:blip'):
                    relationship = document.part.rels.get(blip.get(qn('r:embed')))
                    if relationship and not relationship.is_external:
                        part = relationship.target_part
                        block = self.picture(part.content_type, part.blob)
                        if block:
                            yield block

    def slide_blocks(self, shapes):
        for shape in shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from self.slide_blocks(shape.shapes)
            elif shape.has_table:
                yield {'table': [[cell.text for cell in row.cells] for row in shape.table.rows]}
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                block = self.picture(shape.image.content_type, shape.image.blob)
                if block:
                    yield block
            elif shape.has_text_frame and shape.text.strip():
                yield {'text': shape.text}


@role_required()
@require_safe
@never_cache
def resource_preview(request, pk):
    resource = get_object_or_404(resources_for(request.user), pk=pk)
    file_format = resource.file_format
    context = {'resource': resource}
    if file_format == 'PDF':
        context['pdf'] = True
        page = request.GET.get('page', '')
        context['pdf_page'] = page if page.isascii() and page.isdigit() and len(page) <= 4 else '1'
    elif file_format in {'DOCX', 'PPTX'}:
        try:
            reader = OfficePreview()
            with resource.file.open('rb') as file:
                if file_format == 'DOCX':
                    context['blocks'] = list(reader.word_blocks(Document(file)))
                else:
                    slides = Presentation(file).slides
                    if slides:
                        page = Paginator(list(slides), 1).get_page(request.GET.get('slide', request.GET.get('page')))
                        context['slide'] = page
                        context['blocks'] = list(reader.slide_blocks(page.object_list[0].shapes))
            context['images_omitted'] = reader.images_omitted
        except Exception as exc:
            logger.warning('Preview unavailable for resource %s (%s).', pk, type(exc).__name__)
            context['error'] = 'This file could not be opened in the reader.'
    else:
        raise Http404
    if request.method == 'GET' and not request.user.is_superuser:
        track_resource(request.user.profile, resource)
    return render(request, 'academy/resource_preview.html', context)


@role_required()
@require_safe
@never_cache
@xframe_options_sameorigin
def preview_pdf(request, pk):
    resource = get_object_or_404(resources_for(request.user), pk=pk, file__iendswith='.pdf')
    try:
        file = resource.file.open('rb')
    except FileNotFoundError as exc:
        raise Http404('File no longer available') from exc
    try:
        if file.read(5) != b'%PDF-':
            raise Http404('Invalid PDF')
        file.seek(0)
        response = FileResponse(file, filename=resource.title + '.pdf', content_type='application/pdf')
    except Exception:
        file.close()
        raise
    response['X-Content-Type-Options'] = 'nosniff'
    return response
