from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
import os

from .models import IDCardRequest, Faculty, Course, Batch
from .forms import (IDCardRequestForm, AdminApprovalForm,
                    FacultyForm, CourseForm, BatchForm)
from .card_generator import generate_id_card_png, generate_id_card_pdf
from .emails import (send_submission_confirmation, send_approval_email,
                      send_rejection_email, send_card_generated_email,
                      send_batch_announcement)
from django.conf import settings


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ── Public ────────────────────────────────────────────────────────────────────

def home(request):
    running  = Batch.objects.filter(status='running').select_related('course','faculty')[:6]
    upcoming = Batch.objects.filter(status='upcoming').select_related('course','faculty')[:6]
    return render(request, 'idcard_app/home.html', {
        'running_batches': running, 'upcoming_batches': upcoming
    })


def batches_public(request):
    running   = Batch.objects.filter(status='running').select_related('course','faculty')
    upcoming  = Batch.objects.filter(status='upcoming').select_related('course','faculty')
    completed = Batch.objects.filter(status='completed').select_related('course','faculty')
    return render(request, 'idcard_app/batches_public.html', {
        'running_batches': running,
        'upcoming_batches': upcoming,
        'completed_batches': completed,
    })


def get_batches_for_course(request):
    """AJAX — return batches for selected course."""
    course_id = request.GET.get('course_id')
    batches = Batch.objects.filter(
        course_id=course_id,
        status__in=['upcoming', 'running']
    ).values('id', 'batch_code', 'status', 'timing', 'start_date')
    data = [
        {
            'id': b['id'],
            'text': f"{b['batch_code']} ({b['status'].title()}) — {b['timing'] or 'Timing TBD'}",
        }
        for b in batches
    ]
    return JsonResponse({'batches': data})


def submit_request(request):
    if request.method == 'POST':
        form = IDCardRequestForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.course:
                obj.course_name = obj.course.name
            if obj.batch:
                obj.batch_info = obj.batch.batch_code
            obj.save()
            messages.success(request, 'Application submitted successfully!')
            send_submission_confirmation(obj)
            return redirect('track_status', pk=obj.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = IDCardRequestForm()
    return render(request, 'idcard_app/submit_request.html', {'form': form})


def track_status(request, pk):
    obj = get_object_or_404(IDCardRequest, pk=pk)
    return render(request, 'idcard_app/track_status.html', {'request_obj': obj})


def track_by_roll(request):
    obj = None
    if request.method == 'POST':
        roll  = request.POST.get('roll_number', '').strip()
        email = request.POST.get('student_email', '').strip()
        if roll and email:
            try:
                obj = IDCardRequest.objects.get(
                    Q(roll_number=roll) | Q(confirmed_roll=roll),
                    student_email=email
                )
            except IDCardRequest.DoesNotExist:
                messages.error(request, 'No request found.')
            except IDCardRequest.MultipleObjectsReturned:
                obj = IDCardRequest.objects.filter(
                    Q(roll_number=roll)|Q(confirmed_roll=roll),
                    student_email=email
                ).latest('submitted_at')
    return render(request, 'idcard_app/track_by_roll.html', {'request_obj': obj})


def download_card(request, pk, format='png'):
    obj = get_object_or_404(IDCardRequest, pk=pk, status='generated')
    if format == 'pdf' and obj.generated_card_pdf:
        fp = os.path.join(settings.MEDIA_ROOT, str(obj.generated_card_pdf))
        if os.path.exists(fp):
            return FileResponse(open(fp,'rb'), as_attachment=True,
                                filename=f"IDCard_{obj.get_display_name()}.pdf")
    elif format == 'png' and obj.generated_card_png:
        fp = os.path.join(settings.MEDIA_ROOT, str(obj.generated_card_png))
        if os.path.exists(fp):
            return FileResponse(open(fp,'rb'), as_attachment=True,
                                filename=f"IDCard_{obj.get_display_name()}.png")
    raise Http404("Card not found")


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('admin_dashboard')
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user and is_admin(user):
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'idcard_app/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ── Admin — ID Requests ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    status_filter = request.GET.get('status', '')
    search_query  = request.GET.get('q', '')
    qs = IDCardRequest.objects.all()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search_query:
        qs = qs.filter(
            Q(student_name__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(student_email__icontains=search_query)
        )
    page_obj = Paginator(qs, 15).get_page(request.GET.get('page'))
    stats = {
        'total':     IDCardRequest.objects.count(),
        'pending':   IDCardRequest.objects.filter(status='pending').count(),
        'approved':  IDCardRequest.objects.filter(status='approved').count(),
        'generated': IDCardRequest.objects.filter(status='generated').count(),
        'rejected':  IDCardRequest.objects.filter(status='rejected').count(),
    }
    return render(request, 'idcard_app/admin_dashboard.html', {
        'page_obj': page_obj, 'stats': stats,
        'status_filter': status_filter, 'search_query': search_query,
    })


@login_required
@user_passes_test(is_admin)
def admin_view_request(request, pk):
    obj = get_object_or_404(IDCardRequest, pk=pk)
    if request.method == 'POST':
        form = AdminApprovalForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.processed_by = request.user
            if not obj.confirmed_name:   obj.confirmed_name   = obj.student_name
            if not obj.confirmed_course: obj.confirmed_course = obj.get_display_course()
            if not obj.confirmed_roll:   obj.confirmed_roll   = obj.roll_number
            if not obj.confirmed_batch:  obj.confirmed_batch  = obj.get_display_batch()
            if obj.status == 'approved':
                obj.approved_at = timezone.now()
                obj.save()
                send_approval_email(obj)
                messages.success(request, f'Request approved. Email sent to {obj.student_email}.')
            elif obj.status == 'rejected':
                obj.save()
                send_rejection_email(obj)
                messages.warning(request, f'Request rejected. Email sent to {obj.student_email}.')
            else:
                obj.save()
                messages.success(request, 'Request updated.')
            return redirect('admin_view_request', pk=pk)
    else:
        initial = {
            'confirmed_name':   obj.student_name,
            'confirmed_course': obj.get_display_course(),
            'confirmed_roll':   obj.roll_number,
            'confirmed_batch':  obj.get_display_batch(),
        }
        form = AdminApprovalForm(instance=obj, initial=initial)
    return render(request, 'idcard_app/admin_view_request.html',
                  {'form': form, 'request_obj': obj})


@login_required
@user_passes_test(is_admin)
def generate_card(request, pk):
    obj = get_object_or_404(IDCardRequest, pk=pk)
    if obj.status != 'approved':
        messages.error(request, 'Must be approved first.')
        return redirect('admin_view_request', pk=pk)
    try:
        png_path = generate_id_card_png(obj)
        obj.generated_card_png = png_path
        pdf_path = generate_id_card_pdf(obj, png_path)
        obj.generated_card_pdf = pdf_path
        obj.status = 'generated'
        obj.save()
        send_card_generated_email(obj)
        messages.success(request, f'ID card generated for {obj.get_display_name()}! Email sent to {obj.student_email}.')
    except Exception as e:
        messages.error(request, f'Error: {e}')
    return redirect('admin_view_request', pk=pk)


@login_required
@user_passes_test(is_admin)
def admin_download_card(request, pk, format='png'):
    obj = get_object_or_404(IDCardRequest, pk=pk, status='generated')
    if format == 'pdf' and obj.generated_card_pdf:
        fp = os.path.join(settings.MEDIA_ROOT, str(obj.generated_card_pdf))
        if os.path.exists(fp):
            return FileResponse(open(fp,'rb'), as_attachment=True,
                                filename=f"IDCard_{obj.get_display_name()}.pdf")
    elif format == 'png' and obj.generated_card_png:
        fp = os.path.join(settings.MEDIA_ROOT, str(obj.generated_card_png))
        if os.path.exists(fp):
            return FileResponse(open(fp,'rb'), as_attachment=True,
                                filename=f"IDCard_{obj.get_display_name()}.png")
    raise Http404


@login_required
@user_passes_test(is_admin)
def quick_action(request, pk):
    if request.method == 'POST':
        obj    = get_object_or_404(IDCardRequest, pk=pk)
        action = request.POST.get('action')
        if action == 'approve' and obj.status == 'pending':
            obj.status = 'approved'; obj.approved_at = timezone.now()
            obj.processed_by = request.user
            if not obj.confirmed_name:   obj.confirmed_name   = obj.student_name
            if not obj.confirmed_course: obj.confirmed_course = obj.get_display_course()
            if not obj.confirmed_roll:   obj.confirmed_roll   = obj.roll_number
            obj.save()
            return JsonResponse({'success': True, 'status': 'approved'})
        elif action == 'reject' and obj.status == 'pending':
            obj.status = 'rejected'; obj.processed_by = request.user; obj.save()
            return JsonResponse({'success': True, 'status': 'rejected'})
    return JsonResponse({'success': False}, status=400)


# ── Admin — Faculty ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_faculty_list(request):
    faculty = Faculty.objects.all()
    return render(request, 'idcard_app/admin_faculty.html', {'faculty_list': faculty})


@login_required
@user_passes_test(is_admin)
def admin_faculty_add(request):
    form = FacultyForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Faculty added successfully!')
        return redirect('admin_faculty_list')
    return render(request, 'idcard_app/admin_faculty_form.html',
                  {'form': form, 'title': 'Add Faculty'})


@login_required
@user_passes_test(is_admin)
def admin_faculty_edit(request, pk):
    obj  = get_object_or_404(Faculty, pk=pk)
    form = FacultyForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Faculty updated!')
        return redirect('admin_faculty_list')
    return render(request, 'idcard_app/admin_faculty_form.html',
                  {'form': form, 'title': 'Edit Faculty', 'obj': obj})


@login_required
@user_passes_test(is_admin)
def admin_faculty_delete(request, pk):
    obj = get_object_or_404(Faculty, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Faculty deleted.')
        return redirect('admin_faculty_list')
    return render(request, 'idcard_app/confirm_delete.html',
                  {'obj': obj, 'title': 'Delete Faculty'})


# ── Admin — Courses ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_course_list(request):
    courses = Course.objects.all()
    return render(request, 'idcard_app/admin_course.html', {'courses': courses})


@login_required
@user_passes_test(is_admin)
def admin_course_add(request):
    form = CourseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course added!')
        return redirect('admin_course_list')
    return render(request, 'idcard_app/admin_course_form.html',
                  {'form': form, 'title': 'Add Course'})


@login_required
@user_passes_test(is_admin)
def admin_course_edit(request, pk):
    obj  = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course updated!')
        return redirect('admin_course_list')
    return render(request, 'idcard_app/admin_course_form.html',
                  {'form': form, 'title': 'Edit Course', 'obj': obj})


@login_required
@user_passes_test(is_admin)
def admin_course_delete(request, pk):
    obj = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Course deleted.')
        return redirect('admin_course_list')
    return render(request, 'idcard_app/confirm_delete.html',
                  {'obj': obj, 'title': 'Delete Course'})


# ── Admin — Batches ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_batch_list(request):
    status_filter = request.GET.get('status', '')
    qs = Batch.objects.select_related('course', 'faculty')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'idcard_app/admin_batch.html',
                  {'batches': qs, 'status_filter': status_filter})


@login_required
@user_passes_test(is_admin)
def admin_batch_add(request):
    form = BatchForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Batch created!')
        return redirect('admin_batch_list')
    return render(request, 'idcard_app/admin_batch_form.html',
                  {'form': form, 'title': 'Add Batch'})


@login_required
@user_passes_test(is_admin)
def admin_batch_edit(request, pk):
    obj  = get_object_or_404(Batch, pk=pk)
    form = BatchForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Batch updated!')
        return redirect('admin_batch_list')
    return render(request, 'idcard_app/admin_batch_form.html',
                  {'form': form, 'title': 'Edit Batch', 'obj': obj})


@login_required
@user_passes_test(is_admin)
def admin_batch_delete(request, pk):
    obj = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Batch deleted.')
        return redirect('admin_batch_list')
    return render(request, 'idcard_app/confirm_delete.html',
                  {'obj': obj, 'title': 'Delete Batch'})


# ── Admin — Batch Announcement Email ─────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def send_batch_email(request, pk):
    """Admin sends batch announcement to all students who ever submitted a request."""
    batch = get_object_or_404(Batch, pk=pk)

    if request.method == 'POST':
        target = request.POST.get('target', 'all')

        if target == 'all':
            emails = list(
                IDCardRequest.objects.values_list('student_email', flat=True).distinct()
            )
        elif target == 'course':
            emails = list(
                IDCardRequest.objects.filter(
                    course=batch.course
                ).values_list('student_email', flat=True).distinct()
            )
        else:
            emails = list(
                IDCardRequest.objects.filter(
                    batch=batch
                ).values_list('student_email', flat=True).distinct()
            )

        # Also include any manually entered extra emails
        extra = request.POST.get('extra_emails', '').strip()
        if extra:
            extra_list = [e.strip() for e in extra.split(',') if '@' in e.strip()]
            emails = list(set(emails + extra_list))

        if not emails:
            messages.warning(request, 'No student emails found to send to.')
            return redirect('admin_batch_list')

        sent = send_batch_announcement(batch, emails)
        messages.success(
            request,
            f'Batch announcement sent to {sent}/{len(emails)} students successfully!'
        )
        return redirect('admin_batch_list')

    # GET — show confirmation form
    total_students = IDCardRequest.objects.values('student_email').distinct().count()
    course_students = IDCardRequest.objects.filter(
        course=batch.course
    ).values('student_email').distinct().count()
    batch_students = IDCardRequest.objects.filter(
        batch=batch
    ).values('student_email').distinct().count()

    return render(request, 'idcard_app/send_batch_email.html', {
        'batch': batch,
        'total_students':  total_students,
        'course_students': course_students,
        'batch_students':  batch_students,
    })


# ═══════════════════════════════════════════════════════════════
# MODULE 1 — BIOMETRIC ATTENDANCE SYSTEM
# ═══════════════════════════════════════════════════════════════

import json
import math
import base64
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import AttendanceLocation, BiometricKey, Attendance
from .forms import AttendanceLocationForm, StudentAttendanceLoginForm


# ── Haversine Distance Calculator ────────────────────────────────────────────

def haversine_distance(lat1, lon1, lat2, lon2):
    """Returns distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


# ── Student Attendance Login ──────────────────────────────────────────────────

def attendance_login(request):
    """Student enters roll number + email to access attendance marking."""
    if request.method == 'POST':
        form = StudentAttendanceLoginForm(request.POST)
        if form.is_valid():
            roll  = form.cleaned_data['roll_number'].strip()
            email = form.cleaned_data['student_email'].strip()
            try:
                student = IDCardRequest.objects.get(
                    Q(roll_number=roll) | Q(confirmed_roll=roll),
                    student_email=email,
                    status__in=['approved', 'generated']
                )
                request.session['attendance_student_id'] = student.pk
                request.session['attendance_student_name'] = student.get_display_name()
                return redirect('attendance_mark')
            except IDCardRequest.DoesNotExist:
                messages.error(request, 'Student not found or not yet approved. Contact admin.')
            except IDCardRequest.MultipleObjectsReturned:
                student = IDCardRequest.objects.filter(
                    Q(roll_number=roll) | Q(confirmed_roll=roll),
                    student_email=email,
                    status__in=['approved', 'generated']
                ).latest('submitted_at')
                request.session['attendance_student_id'] = student.pk
                request.session['attendance_student_name'] = student.get_display_name()
                return redirect('attendance_mark')
    else:
        form = StudentAttendanceLoginForm()
    return render(request, 'idcard_app/attendance_login.html', {'form': form})


def attendance_mark(request):
    """Main attendance marking page — GPS + WebAuthn fingerprint."""
    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return redirect('attendance_login')

    try:
        student = IDCardRequest.objects.get(pk=student_id)
    except IDCardRequest.DoesNotExist:
        del request.session['attendance_student_id']
        return redirect('attendance_login')

    locations = AttendanceLocation.objects.filter(is_active=True)

    # Today's attendance for this student
    today = timezone.now().date()
    today_records = Attendance.objects.filter(student=student, date=today).select_related('location')

    # Check if already registered biometric
    has_biometric = BiometricKey.objects.filter(student=student).exists()

    return render(request, 'idcard_app/attendance_mark.html', {
        'student':       student,
        'locations':     locations,
        'today_records': today_records,
        'has_biometric': has_biometric,
        'today':         today,
    })


def attendance_logout(request):
    request.session.pop('attendance_student_id', None)
    request.session.pop('attendance_student_name', None)
    return redirect('attendance_login')


# ── WebAuthn Registration ─────────────────────────────────────────────────────

@csrf_exempt
def webauthn_register_begin(request):
    """Generate WebAuthn registration options (challenge) for student."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    try:
        student = IDCardRequest.objects.get(pk=student_id)
    except IDCardRequest.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)

    # Generate a random challenge
    challenge = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
    request.session['webauthn_challenge'] = challenge

    options = {
        'challenge': challenge,
        'rp': {
            'name': 'NIT Attendance',
            'id':   request.get_host().split(':')[0],
        },
        'user': {
            'id':          base64.urlsafe_b64encode(str(student.pk).encode()).rstrip(b'=').decode(),
            'name':        student.student_email,
            'displayName': student.get_display_name(),
        },
        'pubKeyCredParams': [
            {'alg': -7,   'type': 'public-key'},   # ES256
            {'alg': -257, 'type': 'public-key'},   # RS256
        ],
        'authenticatorSelection': {
            'authenticatorAttachment': 'platform',
            'userVerification':        'required',
        },
        'timeout': 60000,
        'attestation': 'none',
    }
    return JsonResponse(options)


@csrf_exempt
def webauthn_register_complete(request):
    """Store WebAuthn credential after successful registration."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    try:
        data    = json.loads(request.body)
        student = IDCardRequest.objects.get(pk=student_id)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    credential_id = data.get('id', '')
    public_key    = data.get('response', {}).get('attestationObject', '')
    device_info   = request.META.get('HTTP_USER_AGENT', '')[:500]

    # Remove old keys for this student (re-registration)
    BiometricKey.objects.filter(student=student).delete()

    BiometricKey.objects.create(
        student       = student,
        credential_id = credential_id,
        public_key    = public_key,
        device_info   = device_info,
    )
    return JsonResponse({'status': 'ok', 'message': 'Fingerprint registered successfully!'})


# ── WebAuthn Authentication ───────────────────────────────────────────────────

@csrf_exempt
def webauthn_auth_begin(request):
    """Generate WebAuthn authentication challenge."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    keys = BiometricKey.objects.filter(student_id=student_id)
    if not keys.exists():
        return JsonResponse({'error': 'No fingerprint registered. Please register first.'}, status=400)

    challenge = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
    request.session['webauthn_challenge'] = challenge

    options = {
        'challenge':        challenge,
        'timeout':          60000,
        'userVerification': 'required',
        'rpId':             request.get_host().split(':')[0],
        'allowCredentials': [
            {'type': 'public-key', 'id': k.credential_id}
            for k in keys
        ],
    }
    return JsonResponse(options)


@csrf_exempt
def webauthn_auth_complete(request):
    """Verify WebAuthn assertion — mark attendance if GPS also valid."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    try:
        data       = json.loads(request.body)
        student    = IDCardRequest.objects.get(pk=student_id)
        loc_id     = data.get('location_id')
        student_lat = float(data.get('latitude',  0))
        student_lon = float(data.get('longitude', 0))
        credential_id = data.get('id', '')
    except Exception as e:
        return JsonResponse({'error': f'Invalid data: {e}'}, status=400)

    # 1 — Verify biometric key exists
    try:
        bio_key = BiometricKey.objects.get(
            student=student, credential_id=credential_id
        )
    except BiometricKey.DoesNotExist:
        return JsonResponse({'error': 'Fingerprint not recognised. Please re-register.'}, status=401)

    # 2 — Verify GPS location
    try:
        location = AttendanceLocation.objects.get(pk=loc_id, is_active=True)
    except AttendanceLocation.DoesNotExist:
        return JsonResponse({'error': 'Invalid location selected.'}, status=400)

    distance = haversine_distance(
        location.latitude, location.longitude,
        student_lat, student_lon
    )

    if distance > location.radius_meters:
        return JsonResponse({
            'error': f'You are {distance:.0f}m away from {location.name}. '
                     f'Must be within {location.radius_meters}m.',
            'distance': round(distance, 1),
        }, status=403)

    # 3 — Check duplicate attendance today
    today = timezone.now().date()
    if Attendance.objects.filter(student=student, date=today, location=location).exists():
        return JsonResponse({
            'error': f'Attendance already marked for {location.name} today.',
        }, status=409)

    # 4 — Mark attendance
    device_info = request.META.get('HTTP_USER_AGENT', '')[:500]
    now_time    = timezone.now()
    # Late if after 10 AM (configurable)
    status = 'late' if now_time.hour >= 10 else 'present'

    attendance = Attendance.objects.create(
        student            = student,
        location           = location,
        date               = today,
        latitude           = student_lat,
        longitude          = student_lon,
        distance_m         = round(distance, 2),
        device_info        = device_info,
        status             = status,
        biometric_verified = True,
    )

    # Update biometric key last used
    bio_key.last_used_at = now_time
    bio_key.sign_count  += 1
    bio_key.save()

    return JsonResponse({
        'status':   'ok',
        'message':  f'Attendance marked! Status: {status.upper()}',
        'distance': round(distance, 1),
        'location': location.name,
        'time':     now_time.strftime('%I:%M %p'),
        'att_status': status,
    })


# ── Student Attendance History ────────────────────────────────────────────────

def attendance_history(request):
    """Student views their own attendance history."""
    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return redirect('attendance_login')

    student = get_object_or_404(IDCardRequest, pk=student_id)
    records = Attendance.objects.filter(student=student).select_related('location')

    # Summary
    total   = records.count()
    present = records.filter(status__in=['present', 'late']).count()
    percent = round((present / total * 100), 1) if total > 0 else 0

    return render(request, 'idcard_app/attendance_history.html', {
        'student':  student,
        'records':  records[:60],
        'total':    total,
        'present':  present,
        'percent':  percent,
    })


# ── Admin — Location Management ───────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_location_list(request):
    locations = AttendanceLocation.objects.all()
    return render(request, 'idcard_app/admin_location.html', {'locations': locations})


@login_required
@user_passes_test(is_admin)
def admin_location_add(request):
    form = AttendanceLocationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Location added!')
        return redirect('admin_location_list')
    return render(request, 'idcard_app/admin_location_form.html',
                  {'form': form, 'title': 'Add Location'})


@login_required
@user_passes_test(is_admin)
def admin_location_edit(request, pk):
    obj  = get_object_or_404(AttendanceLocation, pk=pk)
    form = AttendanceLocationForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Location updated!')
        return redirect('admin_location_list')
    return render(request, 'idcard_app/admin_location_form.html',
                  {'form': form, 'title': 'Edit Location', 'obj': obj})


@login_required
@user_passes_test(is_admin)
def admin_location_delete(request, pk):
    obj = get_object_or_404(AttendanceLocation, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Location deleted.')
        return redirect('admin_location_list')
    return render(request, 'idcard_app/confirm_delete.html',
                  {'obj': obj, 'title': 'Delete Location'})


@login_required
@user_passes_test(is_admin)
def admin_attendance_report(request):
    """Admin views attendance records with filters."""
    date_filter     = request.GET.get('date', '')
    location_filter = request.GET.get('location', '')
    search          = request.GET.get('q', '')

    qs = Attendance.objects.select_related('student', 'location').all()

    if date_filter:
        qs = qs.filter(date=date_filter)
    if location_filter:
        qs = qs.filter(location_id=location_filter)
    if search:
        qs = qs.filter(
            Q(student__student_name__icontains=search) |
            Q(student__roll_number__icontains=search)
        )

    page_obj  = Paginator(qs, 20).get_page(request.GET.get('page'))
    locations = AttendanceLocation.objects.all()

    # Stats
    today = timezone.now().date()
    stats = {
        'today_total':   Attendance.objects.filter(date=today).count(),
        'today_present': Attendance.objects.filter(date=today, status__in=['present','late']).count(),
        'all_time':      Attendance.objects.count(),
    }

    return render(request, 'idcard_app/admin_attendance_report.html', {
        'page_obj':       page_obj,
        'locations':      locations,
        'stats':          stats,
        'date_filter':    date_filter,
        'location_filter':location_filter,
        'search':         search,
    })


# ═══════════════════════════════════════════════════════════════
# MODULE 2 — SMART CLASS SCHEDULE ATTENDANCE
# ═══════════════════════════════════════════════════════════════

from .models import ClassSchedule, ScheduleAttendance
from .forms  import ClassScheduleForm


# ── Helper: get active schedules for student right now ───────────────────────

def _get_active_schedules_for_student(student):
    """
    Return ClassSchedule queryset that:
    1. Belongs to student's batch
    2. Is scheduled for today's weekday
    3. Current time is within start_time–end_time window
    """
    from django.utils import timezone as tz
    now     = tz.localtime(tz.now())
    weekday = now.weekday()           # 0=Monday … 6=Sunday
    t_now   = now.time()

    batch = student.batch  # FK to Batch
    if not batch:
        return ClassSchedule.objects.none()

    return ClassSchedule.objects.filter(
        batch       = batch,
        day_of_week = weekday,
        start_time__lte = t_now,
        end_time__gte   = t_now,
        is_active   = True,
    ).select_related('batch', 'teacher', 'location')


def _get_todays_schedules_for_student(student):
    """All schedules for today (for display — not limited to active window)."""
    from django.utils import timezone as tz
    weekday = tz.localtime(tz.now()).weekday()
    batch   = student.batch
    if not batch:
        return ClassSchedule.objects.none()
    return ClassSchedule.objects.filter(
        batch=batch, day_of_week=weekday, is_active=True
    ).select_related('teacher', 'location').order_by('start_time')


# ── Student: View today's schedule ───────────────────────────────────────────

def schedule_today(request):
    """Student sees today's class schedule and can mark attendance per class."""
    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return redirect('attendance_login')

    student  = get_object_or_404(IDCardRequest, pk=student_id)
    today    = timezone.localtime(timezone.now()).date()
    now_time = timezone.localtime(timezone.now()).time()

    # All classes scheduled today for this batch
    todays   = _get_todays_schedules_for_student(student)

    # Which ones already have attendance marked today
    marked_ids = set(
        ScheduleAttendance.objects.filter(
            student=student, date=today
        ).values_list('schedule_id', flat=True)
    )

    schedule_data = []
    for sch in todays:
        is_open    = sch.start_time <= now_time <= sch.end_time
        is_past    = now_time > sch.end_time
        is_future  = now_time < sch.start_time
        already    = sch.pk in marked_ids
        att_record = None
        if already:
            try:
                att_record = ScheduleAttendance.objects.get(schedule=sch, student=student, date=today)
            except ScheduleAttendance.DoesNotExist:
                pass
        schedule_data.append({
            'schedule':   sch,
            'is_open':    is_open,
            'is_past':    is_past,
            'is_future':  is_future,
            'already':    already,
            'att_record': att_record,
        })

    return render(request, 'idcard_app/schedule_today.html', {
        'student':       student,
        'schedule_data': schedule_data,
        'today':         today,
        'now_time':      now_time,
    })


# ── AJAX: Mark schedule attendance (GPS + biometric via WebAuthn) ─────────────

@csrf_exempt
def schedule_mark_attendance(request):
    """
    POST endpoint called from JS after WebAuthn auth completes.
    Validates:  1) schedule is currently active   2) GPS inside radius
    Then creates ScheduleAttendance record.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    try:
        data        = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        student_lat = float(data.get('latitude',  0))
        student_lon = float(data.get('longitude', 0))
        credential_id = data.get('credential_id', '')
        student     = IDCardRequest.objects.get(pk=student_id)
    except Exception as e:
        return JsonResponse({'error': f'Invalid data: {e}'}, status=400)

    # 1 — Verify biometric key exists
    if credential_id:
        bio_ok = BiometricKey.objects.filter(student=student, credential_id=credential_id).exists()
        if not bio_ok:
            return JsonResponse({'error': 'Fingerprint not recognised.'}, status=401)

    # 2 — Fetch schedule
    try:
        schedule = ClassSchedule.objects.select_related('location').get(pk=schedule_id, is_active=True)
    except ClassSchedule.DoesNotExist:
        return JsonResponse({'error': 'Class schedule not found.'}, status=404)

    # 3 — Check time window
    now      = timezone.localtime(timezone.now())
    now_time = now.time()
    weekday  = now.weekday()

    if schedule.day_of_week != weekday:
        return JsonResponse({'error': f'This class is scheduled for {schedule.get_day_name()}, not today.'}, status=403)

    if not (schedule.start_time <= now_time <= schedule.end_time):
        return JsonResponse({
            'error': f'Attendance window closed. Class is {schedule.start_time:%I:%M %p}–{schedule.end_time:%I:%M %p}.'
        }, status=403)

    # 4 — Verify GPS
    location = schedule.location
    if not location:
        return JsonResponse({'error': 'No location defined for this class.'}, status=400)

    distance = haversine_distance(location.latitude, location.longitude, student_lat, student_lon)
    if distance > location.radius_meters:
        return JsonResponse({
            'error': (f'You are {distance:.0f}m from {location.name}. '
                      f'Must be within {location.radius_meters}m.'),
            'distance': round(distance, 1),
            'status': 'rejected',
        }, status=403)

    # 5 — Duplicate check
    today = now.date()
    if ScheduleAttendance.objects.filter(schedule=schedule, student=student, date=today).exists():
        return JsonResponse({'error': 'Attendance already marked for this class today.'}, status=409)

    # 6 — Determine present / late
    grace_minutes = 10
    late_threshold = (
        timezone.datetime.combine(today, schedule.start_time) +
        timezone.timedelta(minutes=grace_minutes)
    ).time()
    att_status = 'late' if now_time > late_threshold else 'present'

    # 7 — Save
    device_info = request.META.get('HTTP_USER_AGENT', '')[:500]
    ScheduleAttendance.objects.create(
        schedule           = schedule,
        student            = student,
        date               = today,
        latitude           = student_lat,
        longitude          = student_lon,
        distance_m         = round(distance, 2),
        status             = att_status,
        biometric_verified = bool(credential_id),
        device_info        = device_info,
    )

    # Update bio key last_used
    if credential_id:
        BiometricKey.objects.filter(student=student, credential_id=credential_id).update(
            last_used_at=now, sign_count=models.F('sign_count') + 1
        )

    return JsonResponse({
        'status':    'ok',
        'message':   f'Attendance marked for {schedule.subject}!',
        'att_status': att_status,
        'location':  location.name,
        'distance':  round(distance, 1),
        'time':      now.strftime('%I:%M %p'),
        'subject':   schedule.subject,
    })


# ── Student: Schedule attendance history ─────────────────────────────────────

def schedule_history(request):
    """Student sees their class-wise attendance history."""
    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return redirect('attendance_login')

    student = get_object_or_404(IDCardRequest, pk=student_id)
    records = ScheduleAttendance.objects.filter(student=student).select_related(
        'schedule__batch', 'schedule__location', 'schedule__teacher'
    )

    total   = records.count()
    present = records.filter(status__in=['present', 'late']).count()
    percent = round(present / total * 100, 1) if total > 0 else 0

    # Subject-wise breakdown
    from django.db.models import Count
    subject_stats = (
        records.values('schedule__subject')
        .annotate(
            total=Count('id'),
            present_count=Count('id', filter=Q(status__in=['present','late']))
        )
        .order_by('schedule__subject')
    )

    return render(request, 'idcard_app/schedule_history.html', {
        'student':       student,
        'records':       records[:80],
        'total':         total,
        'present':       present,
        'percent':       percent,
        'subject_stats': subject_stats,
    })


# ── Admin: Schedule CRUD ──────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_schedule_list(request):
    day_filter   = request.GET.get('day', '')
    batch_filter = request.GET.get('batch', '')

    qs = ClassSchedule.objects.select_related('batch__course', 'teacher', 'location')
    if day_filter != '':
        qs = qs.filter(day_of_week=day_filter)
    if batch_filter:
        qs = qs.filter(batch_id=batch_filter)

    batches = Batch.objects.filter(status__in=['running', 'upcoming']).select_related('course')
    now     = timezone.localtime(timezone.now())
    weekday = now.weekday()
    now_t   = now.time()

    # Tag which schedules are live right now
    schedule_list = []
    for s in qs:
        is_live = (s.day_of_week == weekday and s.start_time <= now_t <= s.end_time)
        schedule_list.append({'schedule': s, 'is_live': is_live})

    return render(request, 'idcard_app/admin_schedule.html', {
        'schedule_list': schedule_list,
        'batches':       batches,
        'day_filter':    day_filter,
        'batch_filter':  batch_filter,
        'day_choices':   ClassSchedule.DAY_CHOICES,
    })


@login_required
@user_passes_test(is_admin)
def admin_schedule_add(request):
    form = ClassScheduleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Class schedule created!')
        return redirect('admin_schedule_list')
    return render(request, 'idcard_app/admin_schedule_form.html',
                  {'form': form, 'title': 'Add Class Schedule'})


@login_required
@user_passes_test(is_admin)
def admin_schedule_edit(request, pk):
    obj  = get_object_or_404(ClassSchedule, pk=pk)
    form = ClassScheduleForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Schedule updated!')
        return redirect('admin_schedule_list')
    return render(request, 'idcard_app/admin_schedule_form.html',
                  {'form': form, 'title': 'Edit Class Schedule', 'obj': obj})


@login_required
@user_passes_test(is_admin)
def admin_schedule_delete(request, pk):
    obj = get_object_or_404(ClassSchedule, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Schedule deleted.')
        return redirect('admin_schedule_list')
    return render(request, 'idcard_app/confirm_delete.html',
                  {'obj': obj, 'title': 'Delete Schedule'})


@login_required
@user_passes_test(is_admin)
def admin_schedule_attendance_report(request):
    """Admin: per-class attendance records."""
    schedule_filter = request.GET.get('schedule', '')
    date_filter     = request.GET.get('date', '')
    search          = request.GET.get('q', '')

    qs = ScheduleAttendance.objects.select_related(
        'student', 'schedule__batch', 'schedule__location', 'schedule__teacher'
    )
    if schedule_filter:
        qs = qs.filter(schedule_id=schedule_filter)
    if date_filter:
        qs = qs.filter(date=date_filter)
    if search:
        qs = qs.filter(
            Q(student__student_name__icontains=search) |
            Q(student__roll_number__icontains=search)
        )

    page_obj  = Paginator(qs, 25).get_page(request.GET.get('page'))
    schedules = ClassSchedule.objects.select_related('batch').order_by('batch__batch_code', 'subject')

    today = timezone.now().date()
    stats = {
        'today_total':   ScheduleAttendance.objects.filter(date=today).count(),
        'today_present': ScheduleAttendance.objects.filter(date=today, status__in=['present','late']).count(),
        'all_time':      ScheduleAttendance.objects.count(),
    }

    return render(request, 'idcard_app/admin_schedule_report.html', {
        'page_obj':       page_obj,
        'schedules':      schedules,
        'stats':          stats,
        'schedule_filter': schedule_filter,
        'date_filter':    date_filter,
        'search':         search,
    })


# ═══════════════════════════════════════════════════════════════
# MODULE 3 — AI ATTENDANCE ANALYTICS
# ═══════════════════════════════════════════════════════════════

from django.db.models import Avg, Count, FloatField, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncDate
import json as _json


def _attendance_percent(present, total):
    """Safe attendance percentage."""
    return round(present / total * 100, 1) if total > 0 else 0.0


@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """
    MODULE 3 — AI Attendance Analytics Dashboard.
    Aggregates data from both Attendance and ScheduleAttendance tables.
    """
    from django.utils import timezone as tz

    today      = tz.now().date()
    month_start = today.replace(day=1)

    # ── 1. Batch-wise attendance percentage ───────────────────────────────────
    batches = Batch.objects.filter(status__in=['running', 'upcoming']).prefetch_related('idcardrequests')

    batch_stats = []
    for b in batches:
        students = b.idcardrequests.filter(status__in=['approved', 'generated'])
        total_students = students.count()
        if total_students == 0:
            continue
        # Count schedule attendance present records for this batch
        sa_total   = ScheduleAttendance.objects.filter(schedule__batch=b).count()
        sa_present = ScheduleAttendance.objects.filter(
            schedule__batch=b, status__in=['present', 'late']
        ).count()
        pct = _attendance_percent(sa_present, sa_total)
        batch_stats.append({
            'batch':    b.batch_code,
            'course':   b.course.name if b.course else '',
            'students': total_students,
            'present':  sa_present,
            'total':    sa_total,
            'pct':      pct,
        })
    batch_stats.sort(key=lambda x: x['pct'])

    # ── 2. Students with low attendance (< 75%) ───────────────────────────────
    low_attendance = []
    all_students = IDCardRequest.objects.filter(status__in=['approved', 'generated']).select_related('batch__course')
    for student in all_students:
        total   = ScheduleAttendance.objects.filter(student=student).count()
        present = ScheduleAttendance.objects.filter(student=student, status__in=['present', 'late']).count()
        if total >= 3:  # only flag students with enough records
            pct = _attendance_percent(present, total)
            if pct < 75:
                low_attendance.append({
                    'student': student,
                    'total':   total,
                    'present': present,
                    'pct':     pct,
                })
    low_attendance.sort(key=lambda x: x['pct'])
    low_attendance = low_attendance[:20]

    # ── 3. Frequently absent students (0 attendance in last 7 days) ───────────
    week_ago = today - __import__('datetime').timedelta(days=7)
    frequently_absent = []
    for student in all_students:
        recent = ScheduleAttendance.objects.filter(student=student, date__gte=week_ago).count()
        scheduled = ScheduleAttendance.objects.filter(student=student).filter(date__gte=week_ago).count()
        total_sch = ClassSchedule.objects.filter(batch=student.batch, is_active=True).count() if student.batch else 0
        if total_sch > 0 and recent == 0:
            frequently_absent.append({'student': student, 'days_missed': 7})
    frequently_absent = frequently_absent[:15]

    # ── 4. Top regular students (highest attendance %) ────────────────────────
    top_students = []
    for student in all_students:
        total   = ScheduleAttendance.objects.filter(student=student).count()
        present = ScheduleAttendance.objects.filter(student=student, status__in=['present', 'late']).count()
        if total >= 5:
            pct = _attendance_percent(present, total)
            if pct >= 75:
                top_students.append({'student': student, 'pct': pct, 'present': present, 'total': total})
    top_students.sort(key=lambda x: -x['pct'])
    top_students = top_students[:10]

    # ── 5. Monthly trend (last 6 months) ──────────────────────────────────────
    import datetime
    monthly_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - datetime.timedelta(days=i * 28)).replace(day=1)
        next_month = (month_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        m_total   = ScheduleAttendance.objects.filter(date__gte=month_date, date__lt=next_month).count()
        m_present = ScheduleAttendance.objects.filter(
            date__gte=month_date, date__lt=next_month, status__in=['present', 'late']
        ).count()
        monthly_data.append({
            'month':   month_date.strftime('%b %Y'),
            'total':   m_total,
            'present': m_present,
            'pct':     _attendance_percent(m_present, m_total),
        })

    # ── 6. Today's stats ──────────────────────────────────────────────────────
    today_total   = ScheduleAttendance.objects.filter(date=today).count()
    today_present = ScheduleAttendance.objects.filter(date=today, status__in=['present', 'late']).count()
    today_late    = ScheduleAttendance.objects.filter(date=today, status='late').count()
    today_absent  = max(0, today_total - today_present)

    # ── 7. Daily attendance for last 14 days (trend line) ─────────────────────
    daily_trend = []
    for i in range(13, -1, -1):
        d = today - __import__('datetime').timedelta(days=i)
        dp = ScheduleAttendance.objects.filter(date=d, status__in=['present', 'late']).count()
        dt = ScheduleAttendance.objects.filter(date=d).count()
        daily_trend.append({'date': d.strftime('%d %b'), 'present': dp, 'total': dt})

    # ── 8. Status breakdown (pie) ─────────────────────────────────────────────
    status_counts = {
        'present':  ScheduleAttendance.objects.filter(status='present').count(),
        'late':     ScheduleAttendance.objects.filter(status='late').count(),
        'absent':   ScheduleAttendance.objects.filter(status='absent').count(),
        'rejected': ScheduleAttendance.objects.filter(status='rejected').count(),
    }

    context = {
        'batch_stats':        batch_stats,
        'low_attendance':     low_attendance,
        'frequently_absent':  frequently_absent,
        'top_students':       top_students,
        'monthly_data':       monthly_data,
        'daily_trend':        daily_trend,
        'status_counts':      status_counts,
        'today_total':        today_total,
        'today_present':      today_present,
        'today_late':         today_late,
        'today_absent':       today_absent,
        # JSON for charts
        'batch_labels_json':  _json.dumps([b['batch'] for b in batch_stats]),
        'batch_pct_json':     _json.dumps([b['pct']   for b in batch_stats]),
        'monthly_labels_json':_json.dumps([m['month'] for m in monthly_data]),
        'monthly_pct_json':   _json.dumps([m['pct']   for m in monthly_data]),
        'monthly_present_json': _json.dumps([m['present'] for m in monthly_data]),
        'daily_labels_json':  _json.dumps([d['date']    for d in daily_trend]),
        'daily_present_json': _json.dumps([d['present'] for d in daily_trend]),
        'daily_total_json':   _json.dumps([d['total']   for d in daily_trend]),
        'status_json':        _json.dumps(list(status_counts.values())),
    }
    return render(request, 'idcard_app/analytics_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def analytics_student_detail(request, pk):
    """Detailed attendance analytics for a single student."""
    student   = get_object_or_404(IDCardRequest, pk=pk)
    records   = ScheduleAttendance.objects.filter(student=student).select_related(
        'schedule__subject', 'schedule__location', 'schedule__teacher'
    ).order_by('-date')

    total   = records.count()
    present = records.filter(status__in=['present', 'late']).count()
    late    = records.filter(status='late').count()
    pct     = _attendance_percent(present, total)

    # Subject breakdown
    from django.db.models import Count
    subject_data = (
        records.values('schedule__subject')
        .annotate(total=Count('id'),
                  present_count=Count('id', filter=Q(status__in=['present','late'])))
        .order_by('schedule__subject')
    )
    subj_labels  = _json.dumps([s['schedule__subject'] for s in subject_data])
    subj_present = _json.dumps([s['present_count'] for s in subject_data])
    subj_total   = _json.dumps([s['total']         for s in subject_data])

    return render(request, 'idcard_app/analytics_student_detail.html', {
        'student':      student,
        'records':      records[:50],
        'total':        total,
        'present':      present,
        'late':         late,
        'pct':          pct,
        'subj_labels':  subj_labels,
        'subj_present': subj_present,
        'subj_total':   subj_total,
        'subject_data': subject_data,
    })


@login_required
@user_passes_test(is_admin)
def analytics_api(request):
    """JSON API for live chart refresh."""
    data_type = request.GET.get('type', 'daily')
    import datetime
    today = __import__('django.utils.timezone', fromlist=['now']).now().date()

    if data_type == 'daily':
        result = []
        for i in range(13, -1, -1):
            d  = today - datetime.timedelta(days=i)
            dp = ScheduleAttendance.objects.filter(date=d, status__in=['present','late']).count()
            dt = ScheduleAttendance.objects.filter(date=d).count()
            result.append({'date': d.strftime('%d %b'), 'present': dp, 'total': dt})
        return JsonResponse({'data': result})

    return JsonResponse({'error': 'Unknown type'}, status=400)


# ═══════════════════════════════════════════════════════════════
# MODULE 4 — ANNOUNCEMENT SYSTEM
# ═══════════════════════════════════════════════════════════════

from .models import Announcement
from .forms  import AnnouncementForm


# ── Admin: Announcement CRUD ──────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_announcement_list(request):
    announcements = Announcement.objects.select_related('batch', 'created_by').all()
    return render(request, 'idcard_app/admin_announcement.html',
                  {'announcements': announcements})


@login_required
@user_passes_test(is_admin)
def admin_announcement_add(request):
    form = AnnouncementForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, f'Announcement "{obj.title}" created and published!')
        return redirect('admin_announcement_list')
    return render(request, 'idcard_app/admin_announcement_form.html',
                  {'form': form, 'title': 'Create Announcement'})


@login_required
@user_passes_test(is_admin)
def admin_announcement_edit(request, pk):
    obj  = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Announcement updated!')
        return redirect('admin_announcement_list')
    return render(request, 'idcard_app/admin_announcement_form.html',
                  {'form': form, 'title': 'Edit Announcement', 'obj': obj})


@login_required
@user_passes_test(is_admin)
def admin_announcement_delete(request, pk):
    obj = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Announcement deleted.')
        return redirect('admin_announcement_list')
    return render(request, 'idcard_app/confirm_delete.html',
                  {'obj': obj, 'title': 'Delete Announcement'})


@login_required
@user_passes_test(is_admin)
def admin_announcement_toggle(request, pk):
    """AJAX quick toggle active/inactive."""
    obj = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        obj.is_active = not obj.is_active
        obj.save()
        return JsonResponse({'status': 'ok', 'is_active': obj.is_active})
    return JsonResponse({'error': 'POST required'}, status=405)


# ── Student: View Announcements ───────────────────────────────────────────────

def student_announcements(request):
    """Student sees announcements relevant to them (global + their batch)."""
    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return redirect('attendance_login')

    student = get_object_or_404(IDCardRequest, pk=student_id)
    batch   = student.batch

    # Show: global announcements (batch=None) + batch-specific
    qs = Announcement.objects.filter(is_active=True).filter(
        Q(batch__isnull=True) | Q(batch=batch)
    ).select_related('batch').order_by('-created_at')

    priority_order = {'urgent': 0, 'high': 1, 'normal': 2}

    return render(request, 'idcard_app/student_announcements.html', {
        'student':       student,
        'announcements': qs,
        'urgent_count':  qs.filter(priority='urgent').count(),
    })


def student_announcement_detail(request, pk):
    """Student reads a single announcement in full."""
    student_id = request.session.get('attendance_student_id')
    if not student_id:
        return redirect('attendance_login')

    student = get_object_or_404(IDCardRequest, pk=student_id)
    batch   = student.batch
    ann     = get_object_or_404(
        Announcement,
        pk=pk,
        is_active=True
    )
    # Verify student can see it
    if ann.batch and ann.batch != batch:
        messages.error(request, 'This announcement is not for your batch.')
        return redirect('student_announcements')

    return render(request, 'idcard_app/student_announcement_detail.html', {
        'student': student,
        'ann':     ann,
    })
