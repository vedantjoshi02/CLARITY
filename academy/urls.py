from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import engagement, paper_frequency, previews, study_tools
from .passwords import StudentPasswordReset

from . import views as v


urlpatterns = [
    path('login/reset/', StudentPasswordReset.as_view(), name='password_reset'),
    path('login/reset/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='academy/password_reset_page.html',
    ), name='password_reset_done'),
    path('login/reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='academy/password_reset_page.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('login/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='academy/password_reset_page.html',
    ), name='password_reset_complete'),
    path('dashboard/my-library/', engagement.personal_library, name='personal_library'),
    path('dashboard/notifications/', engagement.notifications, name='notifications'),
    path('dashboard/notifications/<int:pk>/read/', engagement.read_notification, name='read_notification'),
    path('resources/<int:pk>/save/', engagement.save_resource, name='save_resource'),
    path('resources/<int:pk>/preview/', previews.resource_preview, name='resource_preview'),
    path('resources/<int:pk>/preview/pdf/', previews.preview_pdf, name='preview_pdf'),
    path('assistant/paper-frequency/', paper_frequency.paper_frequency, name='paper_frequency'),
    path('assistant/quiz/', study_tools.quiz_view, name='quiz'),
    path('assistant/summarize/', study_tools.written_tool, {'tool': 'summary'}, name='summary'),
    path('assistant/evaluate/', study_tools.written_tool, {'tool': 'evaluation'}, name='evaluation'),
    path('manage/analytics/', engagement.analytics, name='analytics'),
    path('manage/announcements/', engagement.announcement, name='announcement'),
    path('manage/resources/bulk/', engagement.bulk_resources, name='bulk_resources'),
    path('manage/resources/review/', engagement.review_resources, name='review_resources'),


    # ======================================
    # GENERAL
    # ======================================

    path(
        '',
        v.home,
        name='home'
    ),

    path(
        'register/',
        v.register,
        name='register'
    ),

    path(
        'login/',
        v.signin,
        name='login'
    ),

    path(
        'admin-login/',
        v.signin,
        {'admin': True},
        name='admin_login'
    ),

    path(
        'logout/',
        v.signout,
        name='logout'
    ),


    # ======================================
    # STUDENT DASHBOARD
    # ======================================

    path(
        'dashboard/',
        v.dashboard,
        name='dashboard'
    ),

    path('dashboard/gpa-calculator/', v.gpa_calculator, name='gpa_calculator'),

    path(
        'subjects/',
        v.subject_list,
        name='subjects'
    ),

    path(
        'subjects/<int:subject_id>/',
        v.resource_list,
        name='subject_resources'
    ),


    # ======================================
    # RESOURCES
    # ======================================

    path(
        'resources/',
        v.resource_list,
        name='resources'
    ),

    path(
        'resources/<int:pk>/',
        v.resource_detail,
        name='resource_detail'
    ),

    path(
        'resources/<int:pk>/download/',
        v.download,
        name='download'
    ),


    # ======================================
    # PROFILE AND AI
    # ======================================

    path(
        'profile/',
        v.profile,
        name='profile'
    ),

    path(
        'assistant/',
        v.assistant,
        name='assistant'
    ),


    # ======================================
    # ADMIN DASHBOARD
    # ======================================

    path(
        'manage/',
        v.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'manage/students/',
        v.students,
        name='students'
    ),

    path(
        'manage/students/<int:pk>/',
        v.profile,
        name='student_profile'
    ),

    path(
        'manage/students/<int:pk>/<str:action>/',
        v.student_action,
        name='student_action'
    ),


    # ======================================
    # ACADEMIC STRUCTURE
    # ======================================

    path(
        'manage/academics/',
        v.academics,
        name='academics'
    ),

    path(
        'manage/academics/<str:kind>/new/',
        v.academic_edit,
        name='academic_new'
    ),

    path(
        'manage/academics/<str:kind>/<int:pk>/',
        v.academic_edit,
        name='academic_edit'
    ),

    path(
        'manage/academics/<str:kind>/<int:pk>/delete/',
        v.academic_delete,
        name='academic_delete'
    ),


    # ======================================
    # RESOURCE MANAGEMENT
    # ======================================

    path(
        'manage/resources/new/',
        v.resource_edit,
        name='resource_new'
    ),

    path(
        'manage/resources/<int:pk>/edit/',
        v.resource_edit,
        name='resource_edit'
    ),

    path(
        'manage/resources/<int:pk>/<str:action>/',
        v.resource_action,
        name='resource_action'
    ),


    # ======================================
    # AJAX: ACADEMIC DROPDOWNS
    # ======================================

    path(
        'manage/ajax/semesters/',
        v.get_semesters,
        name='get_semesters'
    ),

    path(
        'manage/ajax/subjects/',
        v.get_subjects,
        name='get_subjects'
    ),


    # ======================================
    # AI MANAGEMENT
    # ======================================

    path(
        'manage/ai/',
        v.ai_management,
        name='ai_management'
    ),

]