from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('idcard_app', '0002_faculty_course_batch'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('radius_meters', models.PositiveIntegerField(default=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='BiometricKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('credential_id', models.TextField(unique=True)),
                ('public_key', models.TextField()),
                ('sign_count', models.BigIntegerField(default=0)),
                ('device_info', models.CharField(blank=True, max_length=500)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='biometric_keys',
                    to='idcard_app.idcardrequest'
                )),
            ],
            options={'ordering': ['-registered_at']},
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('time', models.TimeField(auto_now_add=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('distance_m', models.FloatField(default=0)),
                ('device_info', models.CharField(blank=True, max_length=500)),
                ('status', models.CharField(
                    choices=[('present','Present'),('late','Late'),('rejected','Rejected')],
                    default='present', max_length=20
                )),
                ('biometric_verified', models.BooleanField(default=False)),
                ('marked_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendances',
                    to='idcard_app.idcardrequest'
                )),
                ('location', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='attendances',
                    to='idcard_app.attendancelocation'
                )),
            ],
            options={
                'ordering': ['-date', '-time'],
                'unique_together': {('student', 'date', 'location')},
            },
        ),
    ]
