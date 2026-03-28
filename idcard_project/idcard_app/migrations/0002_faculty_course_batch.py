from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('idcard_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Faculty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('designation', models.CharField(blank=True, max_length=200)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='faculty/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name'], 'verbose_name_plural': 'Faculty'},
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('short_name', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField(blank=True)),
                ('duration', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('batch_code', models.CharField(max_length=50, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('timing', models.CharField(blank=True, max_length=100)),
                ('total_seats', models.PositiveIntegerField(default=30)),
                ('status', models.CharField(choices=[('upcoming','Upcoming'),('running','Running'),('completed','Completed')], default='upcoming', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='idcard_app.course')),
                ('faculty', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='batches', to='idcard_app.faculty')),
            ],
            options={'ordering': ['-start_date'], 'verbose_name_plural': 'Batches'},
        ),
        migrations.AddField(
            model_name='idcardrequest',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='idcardrequests', to='idcard_app.course'),
        ),
        migrations.AddField(
            model_name='idcardrequest',
            name='batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='idcardrequests', to='idcard_app.batch'),
        ),
    ]
