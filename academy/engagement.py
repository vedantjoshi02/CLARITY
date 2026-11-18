from datetime import timedelta
from pathlib import Path

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import resources_for, role_required
from .forms import AnnouncementForm, BulkResourceForm
from .models import ActivityLog, ChatHistory, Notification, NotificationRead, Resource, ResourceReading, StudentProfile, Subject


def track_resource(student, resource):
    ResourceReading.objects.update_or_create(
        student=student, resource=resource, defaults={'viewed_at': timezone.now()},
    )


def student_library(user):
    resources = resources_for(user)
    saved = resources.filter(readers__student=user.profile, readers__saved_at__isnull=False)
    viewed = resources.filter(readers__student=user.profile, readers__viewed_at__isnull=False)
    return saved.order_by('-readers__saved_at', '-pk'), viewed.order_by('-readers__viewed_at', '-pk')


@role_required()
def personal_library(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    saved, viewed = student_library(request.user)
    showing_recent = request.GET.get('tab') == 'recent'
    page = Paginator(viewed if showing_recent else saved, 12).get_page(request.GET.get('page'))
    return render(request, 'academy/personal_library.html', {'page': page, 'showing_recent': showing_recent})


@role_required()
@require_POST
def save_resource(request, pk):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    resource = get_object_or_404(resources_for(request.user), pk=pk)
    if request.POST.get('action') == 'remove':
        ResourceReading.objects.filter(student=request.user.profile, resource=resource).update(saved_at=None)
        messages.success(request, 'Removed from My Library.')
    else:
        ResourceReading.objects.update_or_create(
            student=request.user.profile, resource=resource, defaults={'saved_at': timezone.now()},
        )
        messages.success(request, 'Saved to My Library.')
    return redirect('resource_detail', pk=pk)


def notification_feed(student):
    return Notification.objects.filter(
        Q(resource__isnull=True, year=student.year)
        | Q(resource__approved=True, resource__subject__semester__year=student.year)
    ).select_related('resource__subject', 'year').annotate(
        is_read=Exists(NotificationRead.objects.filter(student=student, notification_id=OuterRef('pk'))),
    )


@role_required()
def notifications(request):
    if request.user.is_superuser:
        return redirect('announcement')
    page = Paginator(notification_feed(request.user.profile), 15).get_page(request.GET.get('page'))
    return render(request, 'academy/notifications.html', {'page': page})


@role_required()
@require_POST
def read_notification(request, pk):
    if request.user.is_superuser:
        return redirect('announcement')
    student = request.user.profile
    notification = get_object_or_404(notification_feed(student), pk=pk)
    NotificationRead.objects.get_or_create(student=student, notification=notification)
    return redirect('notifications')


@role_required(admin=True)
def announcement(request):
    form = AnnouncementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            notice = Notification.objects.create(**form.cleaned_data)
            ActivityLog.objects.create(actor=request.user, action=f'Announcement sent to {notice.year}')
        messages.success(request, f'Announcement sent to {notice.year}.')
        return redirect('announcement')
    recent = Notification.objects.filter(resource__isnull=True).select_related('year')[:10]
    return render(request, 'academy/announcement.html', {'form': form, 'recent': recent})


@role_required(admin=True)
def bulk_resources(request):
    form = BulkResourceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        stored_files = []
        try:
            with transaction.atomic():
                for file in data['files']:
                    title = Path(file.name).stem[:180]
                    resource = Resource(
                        subject=data['subject'], kind=data['kind'],
                        title=title, uploaded_by=request.user, approved=False,
                    )
                    resource.file.save(file.name, file, save=False)
                    stored_files.append((resource.file.storage, resource.file.name))
                    resource.save()
                ActivityLog.objects.create(actor=request.user, action=f'Bulk uploaded {len(stored_files)} drafts')
        except Exception:
            for storage, name in stored_files:
                storage.delete(name)
            raise
        messages.success(request, f'{len(stored_files)} documents added to the review queue.')
        return redirect('review_resources')
    return render(request, 'academy/bulk_resources.html', {'form': form})


@role_required(admin=True)
def review_resources(request):
    drafts = Resource.objects.filter(approved=False).select_related('subject__semester__year')
    page = Paginator(drafts.order_by('-created_at', '-pk'), 12).get_page(request.GET.get('page'))
    return render(request, 'academy/review_resources.html', {'page': page})


@role_required(admin=True)
def analytics(request):
    now = timezone.now()
    period = now - timedelta(days=30)
    week = now - timedelta(days=7)
    recent_views = ResourceReading.objects.filter(viewed_at__gte=week)
    recent_questions = ChatHistory.objects.filter(created_at__gte=week)
    active_students = StudentProfile.objects.filter(user__is_active=True).alias(
        viewed_recently=Exists(recent_views.filter(student_id=OuterRef('pk'))),
        asked_recently=Exists(recent_questions.filter(user_id=OuterRef('user_id'))),
    ).filter(Q(user__last_login__gte=week) | Q(viewed_recently=True) | Q(asked_recently=True)).count()
    uploads = Resource.objects.filter(created_at__gte=period)
    upload_days = uploads.annotate(day=TruncDate('created_at')).values('day').annotate(total=Count('pk')).order_by('-day')
    upload_types = uploads.values('kind').annotate(total=Count('pk')).order_by('-total', 'kind')
    type_labels = dict(Resource.TYPES)
    subjects = Subject.objects.select_related('semester__year').annotate(
        published=Count('resources', filter=Q(resources__approved=True)),
        drafts=Count('resources', filter=Q(resources__approved=False)),
    ).order_by('published', 'semester__number', 'name')
    context = {
        'active_students': active_students,
        'viewing_students': recent_views.values('student').distinct().count(),
        'recent_ai_questions': recent_questions.count(),
        'upload_count': uploads.count(),
        'upload_days': upload_days,
        'upload_types': [(type_labels.get(row['kind'], row['kind']), row['total']) for row in upload_types],
        'most_downloaded': Resource.objects.select_related('subject').filter(download_count__gt=0).order_by('-download_count', 'pk')[:10],
        'page': Paginator(subjects, 20).get_page(request.GET.get('page')),
    }
    return render(request, 'academy/analytics.html', context)
