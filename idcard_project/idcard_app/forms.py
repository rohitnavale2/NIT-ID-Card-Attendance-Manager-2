from django import forms
from .models import IDCardRequest, Faculty, Course, Batch, AttendanceLocation, ClassSchedule, Announcement


class IDCardRequestForm(forms.ModelForm):
    """Student-facing form — course & batch are dropdowns only, no free text."""

    class Meta:
        model  = IDCardRequest
        fields = [
            'student_name', 'student_email', 'student_phone',
            'roll_number', 'course', 'batch',
            'student_photo', 'payment_receipt',
        ]
        widgets = {
            'student_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'student_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'student_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9XXXXXXXXX'}),
            'roll_number':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CUS315015'}),
            'course':        forms.Select(attrs={'class': 'form-select', 'id': 'id_course'}),
            'batch':         forms.Select(attrs={'class': 'form-select', 'id': 'id_batch'}),
            'student_photo':   forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'payment_receipt': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'student_name':    'Full Name',
            'student_email':   'Email Address',
            'student_phone':   'Phone Number',
            'roll_number':     'Roll Number / Student ID',
            'course':          'Course',
            'batch':           'Batch',
            'student_photo':   'Passport Size Photo',
            'payment_receipt': 'Payment Receipt (₹100 ID card fee)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        self.fields['course'].empty_label = '— Select Course —'
        self.fields['batch'].queryset  = Batch.objects.filter(status__in=['upcoming', 'running']).select_related('course', 'faculty')
        self.fields['batch'].empty_label = '— Select Batch —'
        self.fields['course'].required = True
        self.fields['batch'].required  = True


class AdminApprovalForm(forms.ModelForm):
    class Meta:
        model  = IDCardRequest
        fields = [
            'confirmed_name', 'confirmed_course', 'confirmed_roll',
            'confirmed_batch', 'valid_till', 'status', 'rejection_reason',
        ]
        widgets = {
            'confirmed_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'confirmed_course': forms.TextInput(attrs={'class': 'form-control'}),
            'confirmed_roll':   forms.TextInput(attrs={'class': 'form-control'}),
            'confirmed_batch':  forms.TextInput(attrs={'class': 'form-control'}),
            'valid_till':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status':           forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FacultyForm(forms.ModelForm):
    class Meta:
        model  = Faculty
        fields = ['name', 'designation', 'email', 'phone', 'photo', 'is_active']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Faculty full name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Trainer'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control'}),
            'photo':       forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model  = Course
        fields = ['name', 'short_name', 'description', 'duration', 'is_active']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full Stack Python'}),
            'short_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. FSP'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6 months'}),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model  = Batch
        fields = ['batch_code', 'course', 'faculty', 'start_date', 'end_date',
                  'timing', 'total_seats', 'status', 'description']
        widgets = {
            'batch_code':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. P4-KV'}),
            'course':       forms.Select(attrs={'class': 'form-select'}),
            'faculty':      forms.Select(attrs={'class': 'form-select'}),
            'start_date':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'timing':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6:00 AM - 7:30 AM'}),
            'total_seats':  forms.NumberInput(attrs={'class': 'form-control'}),
            'status':       forms.Select(attrs={'class': 'form-select'}),
            'description':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].queryset   = Faculty.objects.filter(is_active=True)
        self.fields['faculty'].empty_label = '— Select Faculty —'
        self.fields['course'].empty_label  = '— Select Course —'


class AttendanceLocationForm(forms.ModelForm):
    class Meta:
        model  = AttendanceLocation
        fields = ['name', 'latitude', 'longitude', 'radius_meters', 'is_active']
        widgets = {
            'name':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Building, Computer Lab'}),
            'latitude':       forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': '17.4239'}),
            'longitude':      forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': '78.4738'}),
            'radius_meters':  forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50'}),
            'is_active':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'radius_meters': 'Students must be within this distance (in meters) to mark attendance.',
            'latitude':      'Use Google Maps to get exact coordinates.',
        }


class StudentAttendanceLoginForm(forms.Form):
    roll_number   = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Roll Number'})
    )
    student_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model  = ClassSchedule
        fields = ['batch', 'subject', 'teacher', 'location',
                  'day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'batch':       forms.Select(attrs={'class': 'form-select'}),
            'subject':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Basics, Django REST Framework'}),
            'teacher':     forms.Select(attrs={'class': 'form-select'}),
            'location':    forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time':  forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time':    forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'batch':       'Batch',
            'subject':     'Subject / Topic',
            'teacher':     'Teacher / Faculty',
            'location':    'Building / Lab',
            'day_of_week': 'Day of Week',
            'start_time':  'Start Time',
            'end_time':    'End Time',
            'is_active':   'Active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset    = Batch.objects.filter(status__in=['running','upcoming']).select_related('course')
        self.fields['teacher'].queryset  = Faculty.objects.filter(is_active=True)
        self.fields['teacher'].empty_label  = '— Select Teacher —'
        self.fields['location'].queryset = AttendanceLocation.objects.filter(is_active=True)
        self.fields['location'].empty_label = '— Select Location —'

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end   = cleaned.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model  = Announcement
        fields = ['title', 'message', 'batch', 'priority', 'is_active']
        widgets = {
            'title':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement title'}),
            'message':   forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your announcement here...'}),
            'batch':     forms.Select(attrs={'class': 'form-select'}),
            'priority':  forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'batch':    'Target Batch (leave blank = All Students)',
            'is_active': 'Visible to students',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset    = Batch.objects.filter(status__in=['running','upcoming']).select_related('course')
        self.fields['batch'].empty_label = '— All Students —'
        self.fields['batch'].required    = False
