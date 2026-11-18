from pathlib import Path
import csv
import hashlib
import time

from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Count, Q, F
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import *
from .forms import *
from .access import *
from .engagement import notification_feed, student_library, track_resource
from .gpa import GRADE_POINTS, SEMESTER_SUBJECTS
from .rag import index_resource, answer_question


# ==========================================
# RATE LIMITING
# ==========================================

def limited(key, maximum, seconds):

    key = hashlib.sha256(key.encode()).hexdigest()

    now = timezone.now()

    with transaction.atomic():

        row, _ = RateLimit.objects.get_or_create(
            key=key,
            defaults={
                'until': now + timedelta(seconds=seconds)
            }
        )

        if row.until < now:

            RateLimit.objects.filter(
                pk=row.pk
            ).update(
                count=0,
                until=now + timedelta(seconds=seconds)
            )

        RateLimit.objects.filter(
            pk=row.pk
        ).update(
            count=F('count') + 1
        )

        row.refresh_from_db()

        return row.count > maximum


# ==========================================
# HOME PAGE
# ==========================================

def home(request):

    return render(
        request,
        'academy/home.html'
    )


# ==========================================
# STUDENT REGISTRATION
# ==========================================

def register(request):

    form = RegistrationForm(
        request.POST or None
    )

    if request.method == 'POST':

        if limited(
            'register:' + request.META.get('REMOTE_ADDR', ''),
            20,
            3600
        ):

            form.add_error(
                None,
                'Too many registrations. Please try later.'
            )

        elif form.is_valid():

            try:

                form.save()

            except IntegrityError:

                form.add_error(
                    None,
                    'This email or enrollment is already registered.'
                )

            else:

                messages.success(
                    request,
                    'Your registration is awaiting administrator approval.'
                    if settings.STUDENT_APPROVAL_REQUIRED
                    else 'Your account is ready. Sign in to start learning.'
                )

                return redirect('login')

    return render(
        request,
        'academy/auth.html',
        {
            'form': form,
            'heading': 'Your next chapter starts here.',
            'register': True
        }
    )


# ==========================================
# LOGIN
# ==========================================

def signin(request, admin=False):

    form = LoginForm(
        request.POST or None
    )

    if admin:

        form.fields['identity'].label = 'Administrator username'

    if request.method == 'POST' and form.is_valid():

        identity = form.cleaned_data['identity'].strip()

        if limited(
            'login:' + request.META.get('REMOTE_ADDR', ''),
            30,
            900
        ):

            form.add_error(
                None,
                'Too many attempts. Please try again in 15 minutes.'
            )

        else:

            username = identity

            if not admin:

                u = User.objects.filter(
                    email__iexact=identity
                ).first()

                username = u.username if u else '__unknown__'

            u = authenticate(
                request,
                username=username,
                password=form.cleaned_data['password']
            )

            if u and (
                (admin and u.is_superuser)
                or
                (
                    not admin
                    and not u.is_staff
                    and hasattr(u, 'profile')
                )
            ):

                login(request, u)

                return redirect(
                    'admin_dashboard' if admin else 'dashboard'
                )

            form.add_error(
                None,
                'The sign-in details are incorrect or your account is inactive.'
            )

    return render(
        request,
        'academy/auth.html',
        {
            'form': form,
            'heading': (
                'Welcome back, administrator.'
                if admin
                else 'A little clarity. A lot of possibility.'
            ),
            'admin_login': admin
        }
    )


# ==========================================
# LOGOUT
# ==========================================

@require_POST
def signout(request):

    logout(request)

    return redirect('home')


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@role_required()
def dashboard(request):

    if request.user.is_superuser:

        return redirect('admin_dashboard')

    subjects = subjects_for(
        request.user
    ).annotate(
        resource_count=Count(
            'resources',
            filter=Q(resources__approved=True)
        )
    )

    resources = resources_for(request.user)
    saved, viewed = student_library(request.user)

    return render(
        request,
        'academy/dashboard.html',
        {
            'subjects': subjects,
            'recent': resources[:4],
            'saved_resources': saved[:4],
            'recently_viewed': viewed[:5],
            'unread_notifications': notification_feed(request.user.profile).filter(is_read=False).count(),
            'resource_count': resources.count(),
            'paper_count': resources.filter(kind='pyp').count(),
            'query_count': ChatHistory.objects.filter(
                user=request.user
            ).count()
        }
    )


@role_required()
def gpa_calculator(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    return render(request, 'academy/gpa_calculator.html', {
        'semester_subjects': SEMESTER_SUBJECTS,
        'grade_points': GRADE_POINTS,
    })


# ==========================================
# SUBJECT LIST
# ==========================================

@role_required()
def subject_list(request):

    subjects = subjects_for(
        request.user
    ).annotate(
        resource_count=Count(
            'resources',
            filter=Q(resources__approved=True)
        )
    )

    semester = request.GET.get('semester', '')

    if semester.isdigit():

        subjects = subjects.filter(
            semester__number=int(semester)
        )

    semesters = (
        Semester.objects.all()
        if request.user.is_superuser
        else request.user.profile.year.semesters.all()
    )

    return render(
        request,
        'academy/subjects.html',
        {
            'subjects': subjects,
            'semesters': semesters,
            'selected_semester': semester
        }
    )


# ==========================================
# RESOURCE LIST
# ==========================================

@role_required()
def resource_list(request, subject_id=None):

    resources = resources_for(request.user)

    subject = None

    if subject_id:

        subject = get_object_or_404(
            subjects_for(request.user),
            pk=subject_id
        )

        resources = resources.filter(
            subject=subject
        )

    q = request.GET.get('q', '').strip()

    kind = request.GET.get('kind', '')

    sid = request.GET.get('subject', '')

    semester = request.GET.get('semester', '')

    if q:

        resources = resources.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(subject__name__icontains=q)
        )

    if kind:

        resources = resources.filter(
            kind=kind
        )

    if sid.isdigit():

        resources = resources.filter(
            subject_id=sid
        )

    if semester.isdigit():

        resources = resources.filter(
            subject__semester__number=semester
        )

    return render(
        request,
        'academy/resources.html',
        {
            'page': Paginator(
                resources,
                12
            ).get_page(request.GET.get('page')),

            'subject': subject,
            'subjects': subjects_for(request.user),
            'types': Resource.TYPES,
            'q': q,
            'kind': kind,
            'sid': sid
        }
    )


# ==========================================
# RESOURCE DETAIL
# ==========================================

@role_required()
def resource_detail(request, pk):

    resource = get_object_or_404(
        resources_for(request.user),
        pk=pk
    )

    is_saved = False
    if not request.user.is_superuser:
        if request.method == 'GET':
            track_resource(request.user.profile, resource)
        is_saved = ResourceReading.objects.filter(
            student=request.user.profile, resource=resource, saved_at__isnull=False,
        ).exists()

    return render(
        request,
        'academy/resource_detail.html',
        {
            'resource': resource,
            'excerpts': resource.chunks.all()[:3] if resource.status == 'ready' else (),
            'is_saved': is_saved
        }
    )


# ==========================================
# DOWNLOAD RESOURCE
# ==========================================

@role_required()
def download(request, pk):

    resource = get_object_or_404(
        resources_for(request.user),
        pk=pk
    )

    try:

        file = resource.file.open('rb')

    except FileNotFoundError:

        raise Http404('File no longer available')

    if request.method == 'GET' and not request.user.is_superuser:
        Resource.objects.filter(pk=resource.pk).update(download_count=F('download_count') + 1)
        track_resource(request.user.profile, resource)

    response = FileResponse(
        file,
        as_attachment=True,
        filename=(
            resource.title
            + Path(resource.file.name).suffix
        )
    )

    response['Cache-Control'] = 'private, no-store'

    response['X-Content-Type-Options'] = 'nosniff'

    return response


# ==========================================
# STUDENT PROFILE
# ==========================================

@role_required()
def profile(request, pk=None):

    if pk:

        if not request.user.is_superuser:

            raise PermissionDenied

        student = get_object_or_404(
            StudentProfile.objects.select_related(
                'user',
                'year'
            ),
            pk=pk
        )

    else:

        if request.user.is_superuser:

            return redirect('admin_dashboard')

        student = request.user.profile

    return render(
        request,
        'academy/profile.html',
        {
            'student': student
        }
    )


# ==========================================
# AI ASSISTANT
# ==========================================

@role_required()
def assistant(request):

    subjects = subjects_for(request.user)

    form = QuestionForm(
        request.POST or None,
        subjects=subjects
    )

    selected = None

    if request.method == 'POST' and form.is_valid():

        if limited(
            f'ai:{request.user.pk}',
            20,
            3600
        ):

            form.add_error(
                None,
                'You have reached 20 questions this hour. Please try again later.'
            )

        else:

            start = time.monotonic()

            d = form.cleaned_data

            answer, sources, provider = answer_question(
                request.user,
                d['subject'],
                d['question'],
                d['marks'],
                d['mode']
            )

            selected = ChatHistory.objects.create(
                user=request.user,
                subject=d['subject'],
                question=d['question'],
                marks=d['marks'],
                mode=d['mode'],
                answer=answer,
                sources=sources
            )

            AIUsage.objects.create(
                chat=selected,
                provider=provider,
                elapsed_ms=int(
                    (time.monotonic() - start) * 1000
                )
            )

            return redirect(
                f'/assistant/?chat={selected.pk}'
            )

    history = ChatHistory.objects.filter(
        user=request.user,
        subject__in=subjects
    )

    if request.GET.get('chat', '').isdigit():

        selected = get_object_or_404(
            history,
            pk=request.GET['chat']
        )

        # Old citations from withdrawn resources
        # are never redisplayed.

        allowed = set(
            resources_for(request.user)
            .filter(approved=True)
            .values_list('pk', flat=True)
        )

        if any(
            s['id'] not in allowed
            for s in selected.sources
        ):

            selected.answer = (
                'One or more source documents have been withdrawn. '
                'Please ask this question again using the current '
                'approved resources.'
            )

            selected.sources = []

    return render(
        request,
        'academy/assistant.html',
        {
            'form': form,
            'history': history[:15],
            'selected': selected,
            'provider': settings.LLM_PROVIDER
        }
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@role_required(admin=True)
def admin_dashboard(request):

    return render(
        request,
        'academy/admin_dashboard.html',
        {
            'student_count': StudentProfile.objects.count(),
            'subject_count': Subject.objects.count(),
            'resource_count': Resource.objects.count(),
            'query_count': ChatHistory.objects.count(),

            'years': AcademicYear.objects.annotate(
                total=Count('students')
            ),

            'recent_students': StudentProfile.objects.select_related(
                'user',
                'year'
            ).order_by(
                '-user__date_joined'
            )[:5],

            'recent': Resource.objects.select_related(
                'subject'
            )[:5],

            'activity': ActivityLog.objects.select_related(
                'actor'
            )[:8]
        }
    )


# ==========================================
# ADMIN STUDENT MANAGEMENT
# ==========================================

@role_required(admin=True)
def students(request):

    qs = StudentProfile.objects.select_related(
        'user',
        'year'
    )

    year = request.GET.get('year', '')

    q = request.GET.get('q', '')

    if year.isdigit():

        qs = qs.filter(
            year__number=year
        )

    if q:

        qs = qs.filter(
            Q(full_name__icontains=q)
            | Q(enrollment__icontains=q)
            | Q(user__email__icontains=q)
        )

    if request.GET.get('export') == 'csv':

        response = HttpResponse(
            content_type='text/csv'
        )

        response['Content-Disposition'] = (
            'attachment; filename="clarity-students.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            'Name',
            'Enrollment',
            'Email',
            'Year',
            'Active',
            'Registered',
            'Last login'
        ])

        def safe(v):

            s = str(v or '')

            return (
                "'" + s
                if s.lstrip().startswith(
                    ('=', '+', '-', '@')
                )
                else s
            )

        for s in qs:

            writer.writerow([
                safe(v)
                for v in [
                    s.full_name,
                    s.enrollment,
                    s.user.email,
                    s.year.label,
                    s.user.is_active,
                    s.user.date_joined,
                    s.user.last_login
                ]
            ])

        ActivityLog.objects.create(
            actor=request.user,
            action=f'Exported student directory (year {year or "all"})'
        )

        return response

    return render(
        request,
        'academy/students.html',
        {
            'page': Paginator(
                qs,
                15
            ).get_page(request.GET.get('page')),

            'year': year,
            'q': q
        }
    )


# ==========================================
# ADMIN STUDENT ACTIONS
# ==========================================

@role_required(admin=True)
def student_action(request, pk, action):

    if action not in [
        'promote',
        'activate',
        'deactivate'
    ]:

        raise Http404

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'year',
            'user'
        ),
        pk=pk
    )

    if action == 'promote' and student.year.number == 4:

        messages.error(
            request,
            'Fourth-year students cannot be promoted further.'
        )

        return redirect(
            'student_profile',
            pk=pk
        )

    if request.method == 'POST':

        expected = request.POST.get(
            'expected_year',
            ''
        )

        with transaction.atomic():

            student = StudentProfile.objects.select_for_update().select_related(
                'year',
                'user'
            ).get(pk=pk)

            if action == 'promote':

                if str(student.year_id) != expected:

                    messages.error(
                        request,
                        'This student’s year changed. Review the profile before trying again.'
                    )

                    return redirect(
                        'student_profile',
                        pk=pk
                    )

                old = student.year

                new = get_object_or_404(
                    AcademicYear,
                    number=old.number + 1
                )

                changed = StudentProfile.objects.filter(
                    pk=pk,
                    year=old
                ).update(
                    year=new
                )

                if not changed:

                    raise PermissionDenied(
                        'The student year changed concurrently.'
                    )

                PromotionHistory.objects.create(
                    student=student,
                    previous_year=old,
                    new_year=new,
                    promoted_by=request.user
                )

            else:

                student.user.is_active = (
                    action == 'activate'
                )

                student.user.save(
                    update_fields=['is_active']
                )

            ActivityLog.objects.create(
                actor=request.user,
                action=f'{action.title()} student: {student.enrollment}'
            )

        messages.success(
            request,
            'Student record updated.'
        )

        return redirect(
            'student_profile',
            pk=pk
        )

    return render(
        request,
        'academy/confirm.html',
        {
            'heading': f'{action.title()} {student.full_name}?',

            'description': (
                f'Current year: {student.year}. '
                +
                (
                    'The student will lose access to their current year '
                    'and gain access to the next year.'
                    if action == 'promote'
                    else 'This changes whether the student can sign in.'
                )
            ),

            'expected_year': student.year_id,

            'back': f'/manage/students/{pk}/'
        }
    )


# ==========================================
# ACADEMIC STRUCTURE
# ==========================================

@role_required(admin=True)
def academics(request):

    years = AcademicYear.objects.prefetch_related(
        'semesters'
    ).order_by('number')

    year_id = request.GET.get('year', '')

    selected_year = (
        years.filter(pk=year_id).first()
        if year_id.isdigit()
        else years.first()
    )

    semesters = (
        selected_year.semesters.all()
        if selected_year
        else Semester.objects.none()
    )

    semester_id = request.GET.get('semester', '')

    selected_semester = (
        semesters.filter(pk=semester_id).first()
        if semester_id.isdigit()
        else semesters.first()
    )

    subjects = Subject.objects.none()

    if selected_semester:

        subjects = Subject.objects.filter(
            semester=selected_semester
        ).order_by('name')

    return render(
        request,
        'academy/academics.html',
        {
            'years': years,
            'selected_year': selected_year,
            'semesters': semesters,
            'selected_semester': selected_semester,
            'subjects': subjects
        }
    )


# ==========================================
# ADD / EDIT SUBJECT
# ==========================================

@role_required(admin=True)
def academic_edit(request, kind, pk=None):

    if kind != 'subject':

        raise Http404

    instance = (
        get_object_or_404(
            Subject,
            pk=pk
        )
        if pk
        else None
    )

    year_id = request.GET.get('year', '')

    semester_id = request.GET.get('semester', '')

    if instance:

        year_id = str(
            instance.semester.year_id
        )

        semester_id = str(
            instance.semester_id
        )

    form = SubjectForm(
        request.POST or None,
        instance=instance
    )

    allowed_semesters = (
        Semester.objects.filter(
            year_id=year_id
        ).order_by('number')
        if year_id.isdigit()
        else Semester.objects.none()
    )

    form.fields['semester'].queryset = allowed_semesters

    if (
        not instance
        and semester_id.isdigit()
        and allowed_semesters.filter(
            pk=semester_id
        ).exists()
    ):

        form.fields['semester'].initial = int(
            semester_id
        )

    if request.method == 'POST' and form.is_valid():

        obj = form.save()

        ActivityLog.objects.create(
            actor=request.user,
            action=f'Saved subject: {obj}'
        )

        messages.success(
            request,
            'Subject saved successfully.'
        )

        return redirect(
            f'/manage/academics/?year={obj.semester.year_id}&semester={obj.semester_id}'
        )

    back = (
        f'/manage/academics/?year={year_id}&semester={semester_id}'
        if year_id and semester_id
        else '/manage/academics/'
    )

    return render(
        request,
        'academy/form.html',
        {
            'form': form,
            'heading': 'Edit subject' if instance else 'Add subject',
            'back': back,
            'academic_subject': True
        }
    )


# ==========================================
# DELETE SUBJECT
# ==========================================

@role_required(admin=True)
def academic_delete(request, kind, pk):

    if kind != 'subject':

        raise Http404

    obj = get_object_or_404(
        Subject,
        pk=pk
    )

    year_id = obj.semester.year_id

    semester_id = obj.semester_id

    if request.method == 'POST':

        label = str(obj)

        try:

            obj.delete()

        except ProtectedError:

            messages.error(
                request,
                'This subject has resources. Delete or reassign those resources before deleting the subject.'
            )

        else:

            ActivityLog.objects.create(
                actor=request.user,
                action=f'Deleted subject: {label}'
            )

            messages.success(
                request,
                'Subject deleted successfully.'
            )

        return redirect(
            f'/manage/academics/?year={year_id}&semester={semester_id}'
        )

    return render(
        request,
        'academy/confirm.html',
        {
            'heading': f'Delete {obj}?',

            'description': (
                'This action cannot be undone. '
                'A subject that still has uploaded resources cannot be deleted.'
            ),

            'back': (
                f'/manage/academics/?year={year_id}&semester={semester_id}'
            )
        }
    )


# ==========================================
# AJAX: GET SEMESTERS FOR SELECTED YEAR
# ==========================================

@role_required(admin=True)
def get_semesters(request):

    year_id = request.GET.get('year', '')

    if not year_id.isdigit():

        return JsonResponse({
            'semesters': []
        })

    semesters = Semester.objects.filter(
        year_id=year_id
    ).order_by('number')

    data = [
        {
            'id': semester.id,
            'name': str(semester)
        }
        for semester in semesters
    ]

    return JsonResponse({
        'semesters': data
    })


# ==========================================
# AJAX: GET SUBJECTS FOR SELECTED SEMESTER
# ==========================================

@role_required(admin=True)
def get_subjects(request):

    semester_id = request.GET.get('semester', '')

    if not semester_id.isdigit():

        return JsonResponse({
            'subjects': []
        })

    subjects = Subject.objects.filter(
        semester_id=semester_id
    ).order_by('name')

    data = [
        {
            'id': subject.id,
            'name': str(subject)
        }
        for subject in subjects
    ]

    return JsonResponse({
        'subjects': data
    })


# ==========================================
# RESOURCE UPLOAD / EDIT
# ==========================================

@role_required(admin=True)
def resource_edit(request, pk=None):

    resource = (
        get_object_or_404(
            Resource,
            pk=pk
        )
        if pk
        else None
    )

    old_file = resource.file.name if resource else None
    prior_uploader = resource.uploaded_by_id if resource else request.user.pk

    form = ResourceForm(
        request.POST or None,
        request.FILES or None,
        instance=resource
    )

    if request.method == 'POST' and form.is_valid():

        resource = form.save(commit=False)

        resource.uploaded_by_id = prior_uploader
        needs_index = not pk or 'file' in form.changed_data
        if needs_index or 'subject' in form.changed_data:
            resource.approved = False
        # Only the review action changes publication. Avoid overwriting counters
        # and approval state on unrelated metadata edits.
        if pk:
            editable = {'subject', 'kind', 'title', 'description', 'file'}
            updates = editable.intersection(form.changed_data)
            if needs_index or 'subject' in updates:
                updates.add('approved')
            if needs_index:
                resource.status = 'pending'
                resource.processing_error = ''
                updates.update({'status', 'processing_error'})
            if updates:
                with transaction.atomic():
                    resource.save(update_fields=updates)
                    if needs_index:
                        resource.chunks.all().delete()
        else:
            resource.save()

        if needs_index:
            index_resource(resource)

        # Remove the previous file if replaced
        if old_file and old_file != resource.file.name:

            resource.file.storage.delete(old_file)

        ActivityLog.objects.create(
            actor=request.user,
            action=f'Saved resource: {resource.title}'
        )

        messages.success(
            request,
            'Resource saved. Check its processing status below.'
        )

        return redirect(
            'resource_detail',
            pk=resource.pk
        )

    return render(
        request,
        'academy/form.html',
        {
            'form': form,
            'heading': 'Edit resource' if pk else 'Upload a resource',
            'upload': True,
            'back': '/resources/'
        }
    )


# ==========================================
# RESOURCE ACTIONS
# ==========================================

@role_required(admin=True)
def resource_action(request, pk, action):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    if action in {'publish', 'withdraw'}:
        return review_action(request, resource, action)

    if action not in ['delete', 'reindex']:

        raise Http404

    if request.method == 'POST':

        title = resource.title

        if action == 'reindex':

            indexed = index_resource(resource)
            ActivityLog.objects.create(actor=request.user, action=f'Reindex resource: {title}')
            if indexed:
                messages.success(request, 'Resource text extracted.')
            else:
                messages.warning(request, 'Text extraction needs attention. Review the document status.')
            return redirect('resource_detail', pk=resource.pk)

        else:

            file = resource.file

            resource.delete()

            file.delete(save=False)

        ActivityLog.objects.create(
            actor=request.user,
            action=f'{action.title()} resource: {title}'
        )

        messages.success(
            request,
            'Resource operation completed.'
        )

        return redirect(
            'resources'
        )

    return render(
        request,
        'academy/confirm.html',
        {
            'heading': f'{action.title()} “{resource.title}”?',

            'description': (
                'Deletion permanently removes the document and its search chunks.'
                if action == 'delete'
                else 'Re-extract and index the document for AI retrieval.'
            ),

            'back': f'/resources/{pk}/'
        }
    )



@require_POST
def review_action(request, resource, action):
    publish = action == 'publish'
    if publish and resource.status == 'pending':
        messages.error(request, 'Extract the document before reviewing it for publication.')
        return redirect('resource_detail', pk=resource.pk)

    with transaction.atomic():
        candidates = Resource.objects.filter(pk=resource.pk, approved=not publish)
        if publish:
            candidates = candidates.exclude(status='pending')
        if candidates.update(approved=publish):
            if publish:
                Notification.objects.get_or_create(resource=resource)
            ActivityLog.objects.create(
                actor=request.user, action=f'{action.title()} resource: {resource.title}',
            )
            messages.success(request, 'Resource published.' if publish else 'Resource returned to the review queue.')
    return redirect('resource_detail', pk=resource.pk)


# ==========================================
# AI MANAGEMENT
# ==========================================

@role_required(admin=True)
def ai_management(request):

    return render(
        request,
        'academy/ai_management.html',
        {
            'total': ChatHistory.objects.count(),

            'students_count': ChatHistory.objects.values(
                'user'
            ).distinct().count(),

            'popular': Subject.objects.annotate(
                total=Count('chathistory')
            ).filter(
                total__gt=0
            ).order_by(
                '-total'
            )[:6],

            'resources': Resource.objects.select_related(
                'subject'
            )[:30],

            'provider': settings.LLM_PROVIDER,

            'ready': Resource.objects.filter(
                status='ready'
            ).count(),

            'failed': Resource.objects.filter(
                status='failed'
            ).count(),

            'outcomes': AIUsage.objects.values(
                'provider'
            ).annotate(
                total=Count('id')
            )
        }
    )
