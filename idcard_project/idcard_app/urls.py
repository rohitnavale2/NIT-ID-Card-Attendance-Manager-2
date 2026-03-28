from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    # Public
    
    path('', lambda request: redirect('login'), name='home'),
    path('batches/',                     views.batches_public,  name='batches_public'),
    path('submit/',                      views.submit_request,  name='submit_request'),
    path('status/<int:pk>/',             views.track_status,    name='track_status'),
    path('track/',                       views.track_by_roll,   name='track_by_roll'),
    path('download/<int:pk>/<str:format>/', views.download_card, name='download_card'),
    path('ajax/batches/',                views.get_batches_for_course, name='ajax_batches'),

    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin — ID requests
    path('admin-panel/',                              views.admin_dashboard,    name='admin_dashboard'),
    path('admin-panel/request/<int:pk>/',             views.admin_view_request, name='admin_view_request'),
    path('admin-panel/request/<int:pk>/generate/',    views.generate_card,      name='generate_card'),
    path('admin-panel/request/<int:pk>/download/<str:format>/', views.admin_download_card, name='admin_download_card'),
    path('admin-panel/request/<int:pk>/quick-action/', views.quick_action,     name='quick_action'),

    # Admin — Faculty
    path('admin-panel/faculty/',              views.admin_faculty_list,   name='admin_faculty_list'),
    path('admin-panel/faculty/add/',          views.admin_faculty_add,    name='admin_faculty_add'),
    path('admin-panel/faculty/<int:pk>/edit/', views.admin_faculty_edit,  name='admin_faculty_edit'),
    path('admin-panel/faculty/<int:pk>/delete/', views.admin_faculty_delete, name='admin_faculty_delete'),

    # Admin — Courses
    path('admin-panel/courses/',              views.admin_course_list,   name='admin_course_list'),
    path('admin-panel/courses/add/',          views.admin_course_add,    name='admin_course_add'),
    path('admin-panel/courses/<int:pk>/edit/', views.admin_course_edit,  name='admin_course_edit'),
    path('admin-panel/courses/<int:pk>/delete/', views.admin_course_delete, name='admin_course_delete'),

    # Admin — Batches
    path('admin-panel/batches/',              views.admin_batch_list,   name='admin_batch_list'),
    path('admin-panel/batches/add/',          views.admin_batch_add,    name='admin_batch_add'),
    path('admin-panel/batches/<int:pk>/edit/', views.admin_batch_edit,  name='admin_batch_edit'),
    path('admin-panel/batches/<int:pk>/delete/', views.admin_batch_delete, name='admin_batch_delete'),
    path('admin-panel/batches/<int:pk>/announce/', views.send_batch_email, name='send_batch_email'),

    # ── Attendance — Student ──────────────────────────────────────────────────
    path('attendance/',          views.attendance_login,   name='attendance_login'),
    path('attendance/mark/',     views.attendance_mark,    name='attendance_mark'),
    path('attendance/logout/',   views.attendance_logout,  name='attendance_logout'),
    path('attendance/history/',  views.attendance_history, name='attendance_history'),

    # ── Attendance — WebAuthn API ─────────────────────────────────────────────
    path('attendance/webauthn/register/begin/',    views.webauthn_register_begin,    name='webauthn_register_begin'),
    path('attendance/webauthn/register/complete/', views.webauthn_register_complete, name='webauthn_register_complete'),
    path('attendance/webauthn/auth/begin/',        views.webauthn_auth_begin,        name='webauthn_auth_begin'),
    path('attendance/webauthn/auth/complete/',     views.webauthn_auth_complete,     name='webauthn_auth_complete'),

    # ── Attendance — Admin ────────────────────────────────────────────────────
    path('admin-panel/locations/',               views.admin_location_list,     name='admin_location_list'),
    path('admin-panel/locations/add/',           views.admin_location_add,      name='admin_location_add'),
    path('admin-panel/locations/<int:pk>/edit/', views.admin_location_edit,     name='admin_location_edit'),
    path('admin-panel/locations/<int:pk>/delete/', views.admin_location_delete, name='admin_location_delete'),
    path('admin-panel/attendance/',              views.admin_attendance_report, name='admin_attendance_report'),

    # ── MODULE 2: Class Schedule — Student ───────────────────────────────────
    path('schedule/',          views.schedule_today,   name='schedule_today'),
    path('schedule/history/',  views.schedule_history, name='schedule_history'),
    path('schedule/mark/',     views.schedule_mark_attendance, name='schedule_mark_attendance'),

    # ── MODULE 2: Class Schedule — Admin ─────────────────────────────────────
    path('admin-panel/schedules/',               views.admin_schedule_list,   name='admin_schedule_list'),
    path('admin-panel/schedules/add/',           views.admin_schedule_add,    name='admin_schedule_add'),
    path('admin-panel/schedules/<int:pk>/edit/', views.admin_schedule_edit,   name='admin_schedule_edit'),
    path('admin-panel/schedules/<int:pk>/delete/', views.admin_schedule_delete, name='admin_schedule_delete'),
    path('admin-panel/schedules/report/',        views.admin_schedule_attendance_report, name='admin_schedule_report'),

    # ── MODULE 3: Analytics ───────────────────────────────────────────────────
    path('admin-panel/analytics/',              views.analytics_dashboard,      name='analytics_dashboard'),
    path('admin-panel/analytics/student/<int:pk>/', views.analytics_student_detail, name='analytics_student_detail'),
    path('admin-panel/analytics/api/',          views.analytics_api,            name='analytics_api'),

    # ── MODULE 4: Announcements — Admin ───────────────────────────────────────
    path('admin-panel/announcements/',               views.admin_announcement_list,   name='admin_announcement_list'),
    path('admin-panel/announcements/add/',           views.admin_announcement_add,    name='admin_announcement_add'),
    path('admin-panel/announcements/<int:pk>/edit/', views.admin_announcement_edit,   name='admin_announcement_edit'),
    path('admin-panel/announcements/<int:pk>/delete/', views.admin_announcement_delete, name='admin_announcement_delete'),
    path('admin-panel/announcements/<int:pk>/toggle/', views.admin_announcement_toggle, name='admin_announcement_toggle'),

    # ── MODULE 4: Announcements — Student ─────────────────────────────────────
    path('announcements/',          views.student_announcements,       name='student_announcements'),
    path('announcements/<int:pk>/', views.student_announcement_detail, name='student_announcement_detail'),
]
