"""
NIT ID Card Portal — Email Notifications
Handles all outgoing emails: submission, approval, rejection, batch announcements.
"""

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone


INST_NAME    = getattr(settings, 'INSTITUTE_NAME',    'Naresh i Technologies')
INST_ADDRESS = getattr(settings, 'INSTITUTE_ADDRESS', 'Ameerpet, Hyderabad - 500016')
INST_PHONE   = getattr(settings, 'INSTITUTE_PHONE',   '040 2374 6666')
INST_WEBSITE = getattr(settings, 'INSTITUTE_WEBSITE', 'www.nareshit.com')


def _base_html(title, body_html, accent='#b91c1c'):
    """Wrap body in a clean branded HTML email shell."""
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ margin:0; padding:0; background:#f3f4f6; font-family:Arial,sans-serif; }}
  .wrap {{ max-width:600px; margin:32px auto; background:#fff;
           border-radius:10px; overflow:hidden;
           box-shadow:0 2px 12px rgba(0,0,0,.08); }}
  .hdr {{ background:{accent}; padding:24px 32px; text-align:center; }}
  .hdr h1 {{ margin:0; color:#fff; font-size:22px; letter-spacing:1px; }}
  .hdr p {{ margin:4px 0 0; color:rgba(255,255,255,.8); font-size:13px; }}
  .body {{ padding:32px; color:#374151; font-size:15px; line-height:1.7; }}
  .body h2 {{ color:{accent}; font-size:18px; margin-top:0; }}
  .info-box {{ background:#f9fafb; border-left:4px solid {accent};
               border-radius:4px; padding:14px 18px; margin:20px 0; }}
  .info-row {{ display:flex; justify-content:space-between;
               padding:6px 0; border-bottom:1px solid #e5e7eb; font-size:14px; }}
  .info-row:last-child {{ border-bottom:none; }}
  .info-label {{ color:#6b7280; font-weight:600; min-width:130px; }}
  .btn {{ display:inline-block; background:{accent}; color:#fff !important;
          padding:12px 28px; border-radius:6px; text-decoration:none;
          font-weight:700; font-size:14px; margin:16px 0; }}
  .badge {{ display:inline-block; padding:4px 14px; border-radius:20px;
            font-size:13px; font-weight:700; }}
  .badge-success {{ background:#dcfce7; color:#14532d; }}
  .badge-warning {{ background:#fef9c3; color:#713f12; }}
  .badge-danger  {{ background:#fee2e2; color:#7f1d1d; }}
  .badge-info    {{ background:#dbeafe; color:#1e3a5f; }}
  .ftr {{ background:#1f2937; padding:20px 32px; text-align:center;
          color:#9ca3af; font-size:12px; }}
  .ftr a {{ color:#eab308; text-decoration:none; }}
  .divider {{ border:none; border-top:1px solid #e5e7eb; margin:20px 0; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>📋 {INST_NAME}</h1>
    <p>Student ID Card Management Portal</p>
  </div>
  <div class="body">
    {body_html}
  </div>
  <div class="ftr">
    <p style="margin:0 0 4px">{INST_NAME} | {INST_ADDRESS}</p>
    <p style="margin:0 0 4px">Ph: {INST_PHONE} |
       <a href="http://{INST_WEBSITE}">{INST_WEBSITE}</a></p>
    <p style="margin:8px 0 0;color:#6b7280;font-size:11px">
      This is an automated email. Please do not reply.
    </p>
  </div>
</div>
</body>
</html>"""


def _send(subject, to_email, html_body, text_body=''):
    """Send a single HTML email. Silently fails if email not configured."""
    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        return False
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body or 'Please view this email in an HTML-capable email client.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False


def _send_bulk(subject, recipient_list, html_body, text_body=''):
    """Send same email to multiple recipients individually."""
    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        return 0
    sent = 0
    for email in recipient_list:
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body or 'Please view in HTML email client.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
            sent += 1
        except Exception as e:
            print(f"[Email Error] {email}: {e}")
    return sent


# ── 1. Submission Confirmation ────────────────────────────────────────────────

def send_submission_confirmation(request_obj):
    """Sent to student immediately after they submit their ID card request."""
    name   = request_obj.student_name
    roll   = request_obj.roll_number
    course = request_obj.get_display_course()
    batch  = request_obj.get_display_batch()
    ref_id = request_obj.pk

    body = f"""
<h2>Application Received! ✅</h2>
<p>Dear <strong>{name}</strong>,</p>
<p>Your ID card request has been <strong>successfully submitted</strong>.
   Our admin team will verify your payment receipt and get back to you within
   <strong>24–48 hours</strong>.</p>

<div class="info-box">
  <div class="info-row"><span class="info-label">Reference ID</span><span>#{ref_id}</span></div>
  <div class="info-row"><span class="info-label">Student Name</span><span>{name}</span></div>
  <div class="info-row"><span class="info-label">Roll Number</span><span>{roll}</span></div>
  <div class="info-row"><span class="info-label">Course</span><span>{course}</span></div>
  <div class="info-row"><span class="info-label">Batch</span><span>{batch or '—'}</span></div>
  <div class="info-row"><span class="info-label">Status</span>
    <span><span class="badge badge-warning">Pending Review</span></span></div>
  <div class="info-row"><span class="info-label">Submitted On</span>
    <span>{request_obj.submitted_at.strftime('%d %b %Y, %I:%M %p')}</span></div>
</div>

<p><strong>What happens next?</strong></p>
<ul style="color:#6b7280;font-size:14px">
  <li>Admin will verify your ₹100 payment receipt</li>
  <li>You will receive an email when your request is approved or rejected</li>
  <li>Once approved, your ID card will be generated automatically</li>
  <li>You can download your card from the portal</li>
</ul>

<p>Keep your Reference ID <strong>#{ref_id}</strong> safe for tracking.</p>
<hr class="divider">
<p style="font-size:13px;color:#6b7280">
  If you have any questions, contact us at {INST_PHONE} or visit {INST_WEBSITE}
</p>"""

    html = _base_html(f'ID Card Application Received — #{ref_id}', body)
    return _send(
        subject=f'[NIT] ID Card Application Received — Ref #{ref_id}',
        to_email=request_obj.student_email,
        html_body=html,
    )


# ── 2. Approval Email ─────────────────────────────────────────────────────────

def send_approval_email(request_obj):
    """Sent to student when admin approves their request."""
    name    = request_obj.get_display_name()
    roll    = request_obj.get_display_roll()
    course  = request_obj.get_display_course()
    batch   = request_obj.get_display_batch()
    ref_id  = request_obj.pk
    valid   = request_obj.valid_till.strftime('%d %b %Y') if request_obj.valid_till else '—'

    body = f"""
<h2>🎉 Your ID Card Request is Approved!</h2>
<p>Dear <strong>{name}</strong>,</p>
<p>Great news! Your ID card request has been <strong>approved</strong> by our admin team.
   Your ID card is being generated and will be ready for download shortly.</p>

<div class="info-box">
  <div class="info-row"><span class="info-label">Reference ID</span><span>#{ref_id}</span></div>
  <div class="info-row"><span class="info-label">Name on Card</span><span>{name}</span></div>
  <div class="info-row"><span class="info-label">Roll Number</span><span>{roll}</span></div>
  <div class="info-row"><span class="info-label">Course</span><span>{course}</span></div>
  <div class="info-row"><span class="info-label">Batch</span><span>{batch or '—'}</span></div>
  <div class="info-row"><span class="info-label">Valid Till</span><span>{valid}</span></div>
  <div class="info-row"><span class="info-label">Status</span>
    <span><span class="badge badge-success">✅ Approved</span></span></div>
</div>

<p>Your ID card (PNG + PDF) will be available for download from the portal once generated.</p>
<p>Visit the portal and use your Reference ID <strong>#{ref_id}</strong> to track and download:</p>

<p style="text-align:center">
  <a href="http://{INST_WEBSITE}" class="btn">Download ID Card →</a>
</p>

<hr class="divider">
<p style="font-size:13px;color:#6b7280">
  Keep your ID card safe. Carry it at all times inside the institute premises.
</p>"""

    html = _base_html('Your ID Card Request is Approved! ✅', body, accent='#16a34a')
    return _send(
        subject=f'[NIT] ✅ ID Card Approved — {name}',
        to_email=request_obj.student_email,
        html_body=html,
    )


# ── 3. Rejection Email ────────────────────────────────────────────────────────

def send_rejection_email(request_obj):
    """Sent to student when admin rejects their request."""
    name   = request_obj.student_name
    ref_id = request_obj.pk
    reason = request_obj.rejection_reason or 'Please contact the institute for details.'

    body = f"""
<h2>ID Card Request Update</h2>
<p>Dear <strong>{name}</strong>,</p>
<p>We're sorry to inform you that your ID card request <strong>#{ref_id}</strong>
   could not be processed at this time.</p>

<div class="info-box" style="border-left-color:#dc2626">
  <div class="info-row"><span class="info-label">Reference ID</span><span>#{ref_id}</span></div>
  <div class="info-row"><span class="info-label">Status</span>
    <span><span class="badge badge-danger">❌ Rejected</span></span></div>
  <div class="info-row"><span class="info-label">Reason</span><span>{reason}</span></div>
</div>

<p><strong>What you can do:</strong></p>
<ul style="color:#6b7280;font-size:14px">
  <li>Review the rejection reason above</li>
  <li>Visit the institute with the correct payment receipt</li>
  <li>Submit a fresh application on the portal</li>
  <li>Contact us at {INST_PHONE} for assistance</li>
</ul>

<hr class="divider">
<p style="font-size:13px;color:#6b7280">
  We apologize for any inconvenience. Please contact reception for assistance.
</p>"""

    html = _base_html('ID Card Request — Status Update', body, accent='#dc2626')
    return _send(
        subject=f'[NIT] ID Card Request #{ref_id} — Action Required',
        to_email=request_obj.student_email,
        html_body=html,
    )


# ── 4. Card Generated Email ───────────────────────────────────────────────────

def send_card_generated_email(request_obj):
    """Sent when the ID card PNG+PDF are actually generated and ready."""
    name   = request_obj.get_display_name()
    roll   = request_obj.get_display_roll()
    ref_id = request_obj.pk

    body = f"""
<h2>🪪 Your ID Card is Ready!</h2>
<p>Dear <strong>{name}</strong>,</p>
<p>Your NIT Student ID Card has been <strong>generated successfully</strong>
   and is now available for download in both <strong>PNG</strong> and <strong>PDF</strong> formats.</p>

<div class="info-box" style="border-left-color:#2563eb">
  <div class="info-row"><span class="info-label">Name</span><span>{name}</span></div>
  <div class="info-row"><span class="info-label">Roll Number</span><span>{roll}</span></div>
  <div class="info-row"><span class="info-label">Reference ID</span><span>#{ref_id}</span></div>
  <div class="info-row"><span class="info-label">Status</span>
    <span><span class="badge badge-info">🪪 Card Ready</span></span></div>
</div>

<p style="text-align:center">
  <a href="http://{INST_WEBSITE}" class="btn">Download Your ID Card →</a>
</p>

<p style="font-size:13px;color:#6b7280;margin-top:20px">
  <strong>Tip:</strong> Print the PDF for best quality. Laminate it for long-term use.
  Always carry your ID card inside the institute premises.
</p>"""

    html = _base_html('🪪 Your NIT ID Card is Ready for Download!', body, accent='#2563eb')
    return _send(
        subject=f'[NIT] 🪪 ID Card Ready — {name} (Roll: {roll})',
        to_email=request_obj.student_email,
        html_body=html,
    )


# ── 5. New Batch Announcement ─────────────────────────────────────────────────

def send_batch_announcement(batch, recipient_emails):
    """
    Broadcast a new batch announcement to a list of student emails.
    recipient_emails: list of email strings
    Returns: number of emails sent successfully
    """
    from django.utils.timezone import localtime

    course_name  = batch.course.name if batch.course else '—'
    faculty_name = batch.faculty.name if batch.faculty else 'To be announced'
    start_date   = batch.start_date.strftime('%d %B %Y')
    end_date     = batch.end_date.strftime('%d %B %Y') if batch.end_date else 'To be announced'
    timing       = batch.timing or 'To be announced'
    seats        = batch.total_seats
    status_badge = {
        'upcoming': '<span class="badge badge-warning">⏳ Upcoming</span>',
        'running':  '<span class="badge badge-success">▶ Running Now</span>',
    }.get(batch.status, '')
    description  = batch.description or ''

    body = f"""
<h2>📢 New Batch Announced!</h2>
<p>We are excited to announce a new batch at <strong>{INST_NAME}</strong>.
   Limited seats available — register early!</p>

<div class="info-box">
  <div class="info-row"><span class="info-label">Batch Code</span>
    <span><strong>{batch.batch_code}</strong></span></div>
  <div class="info-row"><span class="info-label">Course</span>
    <span><strong>{course_name}</strong></span></div>
  <div class="info-row"><span class="info-label">Faculty</span><span>{faculty_name}</span></div>
  <div class="info-row"><span class="info-label">Start Date</span><span>{start_date}</span></div>
  <div class="info-row"><span class="info-label">End Date</span><span>{end_date}</span></div>
  <div class="info-row"><span class="info-label">Timing</span><span>{timing}</span></div>
  <div class="info-row"><span class="info-label">Total Seats</span><span>{seats}</span></div>
  <div class="info-row"><span class="info-label">Status</span><span>{status_badge}</span></div>
</div>

{'<p style="color:#374151">' + description + '</p>' if description else ''}

<p><strong>How to enroll:</strong></p>
<ol style="color:#6b7280;font-size:14px">
  <li>Visit the institute at {INST_ADDRESS}</li>
  <li>Pay ₹100 ID card fee at reception</li>
  <li>Submit your ID card application on the portal</li>
</ol>

<p style="text-align:center">
  <a href="http://{INST_WEBSITE}" class="btn">View All Batches →</a>
</p>

<hr class="divider">
<p style="font-size:12px;color:#9ca3af;text-align:center">
  You are receiving this because you are a registered student at {INST_NAME}.<br>
  Contact us at {INST_PHONE} for more information.
</p>"""

    html = _base_html(
        f'New Batch: {batch.batch_code} — {course_name}', body, accent='#b91c1c'
    )
    subject = f'[NIT] 📢 New Batch Announced: {batch.batch_code} — {course_name}'
    return _send_bulk(subject, recipient_emails, html)
