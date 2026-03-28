from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('idcard_app', '0003_attendance'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('subject', models.CharField(max_length=200)),
                ('day_of_week', models.IntegerField(
                    choices=[(0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),
                             (3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday')],
                    default=0
                )),
                ('start_time', models.TimeField()),
                ('end_time',   models.TimeField()),
                ('is_active',  models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='schedules',
                    to='idcard_app.batch'
                )),
                ('teacher', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='schedules',
                    to='idcard_app.faculty'
                )),
                ('location', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='schedules',
                    to='idcard_app.attendancelocation'
                )),
            ],
            options={
                'verbose_name': 'Class Schedule',
                'ordering': ['day_of_week', 'start_time'],
            },
        ),
        migrations.CreateModel(
            name='ScheduleAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('date',        models.DateField(default=django.utils.timezone.now)),
                ('marked_at',   models.DateTimeField(auto_now_add=True)),
                ('latitude',    models.FloatField()),
                ('longitude',   models.FloatField()),
                ('distance_m',  models.FloatField(default=0)),
                ('status', models.CharField(
                    choices=[('present','Present'),('late','Late'),
                             ('absent','Absent'),('rejected','Rejected — Outside Location')],
                    default='present', max_length=20
                )),
                ('biometric_verified', models.BooleanField(default=False)),
                ('device_info', models.CharField(blank=True, max_length=500)),
                ('remarks',     models.CharField(blank=True, max_length=300)),
                ('schedule', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendances',
                    to='idcard_app.classschedule'
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='schedule_attendances',
                    to='idcard_app.idcardrequest'
                )),
            ],
            options={
                'verbose_name': 'Schedule Attendance',
                'ordering': ['-date', '-marked_at'],
                'unique_together': {('schedule', 'student', 'date')},
            },
        ),
    ]
