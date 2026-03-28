from django.contrib import admin
from .models import IDCardRequest, Faculty, Course, Batch


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display  = ['name', 'designation', 'email', 'phone', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name', 'email']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ['name', 'short_name', 'duration', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display  = ['batch_code', 'course', 'faculty', 'start_date', 'status', 'total_seats']
    list_filter   = ['status', 'course']
    search_fields = ['batch_code']
    ordering      = ['-start_date']


@admin.register(IDCardRequest)
class IDCardRequestAdmin(admin.ModelAdmin):
    list_display  = ['student_name', 'roll_number', 'course', 'batch', 'status', 'submitted_at']
    list_filter   = ['status', 'submitted_at']
    search_fields = ['student_name', 'roll_number', 'student_email']
    readonly_fields = ['submitted_at', 'updated_at', 'approved_at']
    ordering      = ['-submitted_at']


from .models import AttendanceLocation, BiometricKey, Attendance


@admin.register(AttendanceLocation)
class AttendanceLocationAdmin(admin.ModelAdmin):
    list_display  = ['name', 'latitude', 'longitude', 'radius_meters', 'is_active']
    list_filter   = ['is_active']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ['student', 'location', 'date', 'time', 'status', 'biometric_verified', 'distance_m']
    list_filter   = ['status', 'date', 'location', 'biometric_verified']
    search_fields = ['student__student_name', 'student__roll_number']
    ordering      = ['-date', '-time']


@admin.register(BiometricKey)
class BiometricKeyAdmin(admin.ModelAdmin):
    list_display  = ['student', 'device_info', 'registered_at', 'last_used_at']
    search_fields = ['student__student_name']


from .models import ClassSchedule, ScheduleAttendance


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display  = ['subject', 'batch', 'teacher', 'location', 'get_day_name', 'start_time', 'end_time', 'is_active']
    list_filter   = ['day_of_week', 'is_active', 'batch']
    search_fields = ['subject', 'batch__batch_code']
    ordering      = ['day_of_week', 'start_time']


@admin.register(ScheduleAttendance)
class ScheduleAttendanceAdmin(admin.ModelAdmin):
    list_display  = ['student', 'schedule', 'date', 'status', 'biometric_verified', 'distance_m']
    list_filter   = ['status', 'date', 'biometric_verified']
    search_fields = ['student__student_name', 'student__roll_number', 'schedule__subject']
    ordering      = ['-date', '-marked_at']


from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display  = ['title', 'priority', 'batch', 'is_active', 'created_by', 'created_at']
    list_filter   = ['priority', 'is_active', 'batch']
    search_fields = ['title', 'message']
    ordering      = ['-created_at']
