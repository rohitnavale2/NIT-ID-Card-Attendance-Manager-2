from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='IDCardRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=200)),
                ('student_email', models.EmailField(max_length=254)),
                ('student_phone', models.CharField(max_length=15)),
                ('course_name', models.CharField(max_length=200)),
                ('roll_number', models.CharField(max_length=50)),
                ('batch_info', models.CharField(blank=True, max_length=100)),
                ('student_photo', models.ImageField(upload_to='photos/')),
                ('payment_receipt', models.ImageField(upload_to='receipts/')),
                ('payment_amount', models.DecimalField(decimal_places=2, default=100.0, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('generated', 'Generated')], default='pending', max_length=20)),
                ('rejection_reason', models.TextField(blank=True)),
                ('confirmed_name', models.CharField(blank=True, max_length=200)),
                ('confirmed_course', models.CharField(blank=True, max_length=200)),
                ('confirmed_roll', models.CharField(blank=True, max_length=50)),
                ('confirmed_batch', models.CharField(blank=True, max_length=100)),
                ('generated_card_pdf', models.FileField(blank=True, null=True, upload_to='generated_cards/')),
                ('generated_card_png', models.ImageField(blank=True, null=True, upload_to='generated_cards/')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('valid_till', models.DateField(blank=True, null=True)),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_requests', to='auth.user')),
            ],
            options={
                'verbose_name': 'ID Card Request',
                'verbose_name_plural': 'ID Card Requests',
                'ordering': ['-submitted_at'],
            },
        ),
    ]
