from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('idcard_app', '0004_class_schedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title',    models.CharField(max_length=300)),
                ('message',  models.TextField()),
                ('priority', models.CharField(
                    choices=[('normal','Normal'),('high','High'),('urgent','Urgent')],
                    default='normal', max_length=10
                )),
                ('is_active',  models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='announcements',
                    to='idcard_app.batch'
                )),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='announcements',
                    to='auth.user'
                )),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Announcement'},
        ),
    ]
