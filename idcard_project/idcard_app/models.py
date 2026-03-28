from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Faculty(models.Model):
    name        = models.CharField(max_length=200)
    designation = models.CharField(max_length=200, blank=True)
    email       = models.EmailField(blank=True)
    phone       = models.CharField(max_length=15, blank=True)
    photo       = models.ImageField(upload_to='faculty/', blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Faculty'

    def __str__(self):
        return self.name


class Course(models.Model):
    name        = models.CharField(max_length=200, unique=True)
    short_name  = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    duration    = models.CharField(max_length=100, blank=True, help_text='e.g. 6 months, 1 year')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Batch(models.Model):
    STATUS_CHOICES = [
        ('upcoming',  'Upcoming'),
        ('running',   'Running'),
        ('completed', 'Completed'),
    ]

    batch_code   = models.CharField(max_length=50, unique=True, help_text='e.g. P4-KV, J5-AM')
    course       = models.ForeignKey(Course,  on_delete=models.CASCADE, related_name='batches')
    faculty      = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    start_date   = models.DateField()
    end_date     = models.DateField(null=True, blank=True)
    timing       = models.CharField(max_length=100, blank=True, help_text='e.g. 6:00 AM - 7:30 AM')
    total_seats  = models.PositiveIntegerField(default=30)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    description  = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Batches'

    def __str__(self):
        return f"{self.batch_code} — {self.course.name}"

    def enrolled_count(self):
        return self.idcardrequests.filter(status__in=['approved', 'generated']).count()

    def available_seats(self):
        return max(0, self.total_seats - self.enrolled_count())

    def status_color(self):
        return {'upcoming': 'warning', 'running': 'success', 'completed': 'secondary'}.get(self.status, 'secondary')


class IDCardRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('generated', 'Generated'),
    ]

    # Student info
    student_name  = models.CharField(max_length=200)
    student_email = models.EmailField()
    student_phone = models.CharField(max_length=15)
    roll_number   = models.CharField(max_length=50)

    # Linked from admin-controlled lists
    course  = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='idcardrequests')
    batch   = models.ForeignKey(Batch,  on_delete=models.SET_NULL, null=True, blank=True, related_name='idcardrequests')

    # Keep plain text fallbacks
    course_name = models.CharField(max_length=200, blank=True)
    batch_info  = models.CharField(max_length=100, blank=True)

    # Photo & receipt
    student_photo   = models.ImageField(upload_to='photos/')
    payment_receipt = models.ImageField(upload_to='receipts/')
    payment_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)

    # Status
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)

    # Admin confirmed fields
    confirmed_name   = models.CharField(max_length=200, blank=True)
    confirmed_course = models.CharField(max_length=200, blank=True)
    confirmed_roll   = models.CharField(max_length=50,  blank=True)
    confirmed_batch  = models.CharField(max_length=100, blank=True)

    # Generated card files
    generated_card_pdf = models.FileField(upload_to='generated_cards/', blank=True, null=True)
    generated_card_png = models.ImageField(upload_to='generated_cards/', blank=True, null=True)

    # Dates
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    approved_at  = models.DateTimeField(null=True, blank=True)
    valid_till   = models.DateField(null=True, blank=True)

    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='processed_requests'
    )

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'ID Card Request'
        verbose_name_plural = 'ID Card Requests'

    def __str__(self):
        return f"{self.student_name} — {self.roll_number} ({self.status})"

    def get_display_name(self):
        return self.confirmed_name or self.student_name

    def get_display_course(self):
        return self.confirmed_course or (self.course.name if self.course else self.course_name)

    def get_display_roll(self):
        return self.confirmed_roll or self.roll_number

    def get_display_batch(self):
        return self.confirmed_batch or (self.batch.batch_code if self.batch else self.batch_info)


# ═══════════════════════════════════════════════════════════════
# MODULE 1 — BIOMETRIC ATTENDANCE SYSTEM
# ═══════════════════════════════════════════════════════════════

class AttendanceLocation(models.Model):
    """Admin-defined institute locations where attendance can be marked."""
    name        = models.CharField(max_length=200, help_text='e.g. Main Building, Computer Lab')
    latitude    = models.FloatField(help_text='GPS latitude of the location center')
    longitude   = models.FloatField(help_text='GPS longitude of the location center')
    radius_meters = models.PositiveIntegerField(default=50, help_text='Allowed radius in meters')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.radius_meters}m radius)"


class BiometricKey(models.Model):
    """Stores WebAuthn public key credential per student device."""
    student         = models.ForeignKey(
        IDCardRequest, on_delete=models.CASCADE, related_name='biometric_keys'
    )
    credential_id   = models.TextField(unique=True, help_text='WebAuthn credential ID (base64url)')
    public_key      = models.TextField(help_text='WebAuthn public key (base64url)')
    sign_count      = models.BigIntegerField(default=0)
    device_info     = models.CharField(max_length=500, blank=True)
    registered_at   = models.DateTimeField(auto_now_add=True)
    last_used_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-registered_at']

    def __str__(self):
        return f"Key for {self.student.student_name} — {self.device_info[:40]}"


class Attendance(models.Model):
    """Records each student attendance event."""
    STATUS_CHOICES = [
        ('present',  'Present'),
        ('late',     'Late'),
        ('rejected', 'Rejected'),
    ]

    student     = models.ForeignKey(
        IDCardRequest, on_delete=models.CASCADE, related_name='attendances'
    )
    location    = models.ForeignKey(
        AttendanceLocation, on_delete=models.SET_NULL,
        null=True, related_name='attendances'
    )
    date        = models.DateField(default=timezone.now)
    time        = models.TimeField(auto_now_add=True)
    latitude    = models.FloatField(help_text='Student GPS latitude at mark time')
    longitude   = models.FloatField(help_text='Student GPS longitude at mark time')
    distance_m  = models.FloatField(default=0, help_text='Distance from location center in meters')
    device_info = models.CharField(max_length=500, blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    biometric_verified = models.BooleanField(default=False)
    marked_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering  = ['-date', '-time']
        unique_together = [['student', 'date', 'location']]

    def __str__(self):
        return f"{self.student.student_name} — {self.date} — {self.status}"


# ═══════════════════════════════════════════════════════════════
# MODULE 2 — SMART CLASS SCHEDULE ATTENDANCE
# ═══════════════════════════════════════════════════════════════

class ClassSchedule(models.Model):
    """Admin-defined class timetable. Attendance can only be marked during active class."""

    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    batch      = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name='schedules',
        help_text='Which batch this class belongs to'
    )
    subject    = models.CharField(max_length=200, help_text='e.g. Python Basics, Django Framework')
    teacher    = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='schedules', help_text='Faculty teaching this class'
    )
    location   = models.ForeignKey(
        AttendanceLocation, on_delete=models.SET_NULL, null=True,
        related_name='schedules', help_text='Building / Lab where class is held'
    )
    day_of_week = models.IntegerField(
        choices=DAY_CHOICES, default=0,
        help_text='Day this schedule repeats every week'
    )
    start_time  = models.TimeField(help_text='Class start time')
    end_time    = models.TimeField(help_text='Class end time')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Class Schedule'

    def __str__(self):
        day = dict(self.DAY_CHOICES).get(self.day_of_week, '')
        return f"{self.batch.batch_code} | {self.subject} | {day} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def get_day_name(self):
        return dict(self.DAY_CHOICES).get(self.day_of_week, '')

    def is_active_now(self):
        """Return True if current day & time falls within this schedule window."""
        import datetime
        now = timezone.localtime(timezone.now())
        if now.weekday() != self.day_of_week:
            return False
        return self.start_time <= now.time() <= self.end_time

    def minutes_until_start(self):
        """Minutes until class starts (negative = already started)."""
        import datetime
        now = timezone.localtime(timezone.now()).time()
        today = timezone.localtime(timezone.now()).date()
        start_dt = timezone.datetime.combine(today, self.start_time)
        now_dt   = timezone.datetime.combine(today, now)
        diff = (start_dt - now_dt).total_seconds() / 60
        return round(diff)


class ScheduleAttendance(models.Model):
    """
    Attendance tied to a specific class schedule.
    One record per student per schedule per date.
    """
    STATUS_CHOICES = [
        ('present',  'Present'),
        ('late',     'Late'),
        ('absent',   'Absent'),
        ('rejected', 'Rejected — Outside Location'),
    ]

    schedule    = models.ForeignKey(
        ClassSchedule, on_delete=models.CASCADE, related_name='attendances'
    )
    student     = models.ForeignKey(
        IDCardRequest, on_delete=models.CASCADE, related_name='schedule_attendances'
    )
    date        = models.DateField(default=timezone.now)
    marked_at   = models.DateTimeField(auto_now_add=True)
    latitude    = models.FloatField()
    longitude   = models.FloatField()
    distance_m  = models.FloatField(default=0)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    biometric_verified = models.BooleanField(default=False)
    device_info = models.CharField(max_length=500, blank=True)
    remarks     = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-date', '-marked_at']
        unique_together = [['schedule', 'student', 'date']]
        verbose_name = 'Schedule Attendance'

    def __str__(self):
        return f"{self.student.get_display_name()} | {self.schedule.subject} | {self.date} | {self.status}"


# ═══════════════════════════════════════════════════════════════
# MODULE 4 — ANNOUNCEMENT SYSTEM
# ═══════════════════════════════════════════════════════════════

class Announcement(models.Model):
    """Admin creates announcements, optionally targeted to a specific batch."""

    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]

    title      = models.CharField(max_length=300)
    message    = models.TextField()
    batch      = models.ForeignKey(
        Batch, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='announcements',
        help_text='Leave blank to send to ALL students'
    )
    priority   = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_active  = models.BooleanField(default=True, help_text='Inactive announcements are hidden from students')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Announcement'

    def __str__(self):
        target = self.batch.batch_code if self.batch else 'All Students'
        return f"[{self.priority.upper()}] {self.title} → {target}"

    def get_target_display(self):
        return self.batch.batch_code if self.batch else 'All Students'
