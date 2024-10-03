# Generated by Django 5.1.1 on 2024-10-03 20:46

import datetime
import django.db.models.deletion
import django.db.models.expressions
import django.db.models.functions.datetime
import main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BotUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=511, verbose_name='Full name')),
                ('username', models.CharField(db_index=True, max_length=511, verbose_name='Username')),
                ('telegram_id', models.CharField(db_index=True, max_length=511, verbose_name='Telegram id')),
                ('role', models.CharField(choices=[('superuser', 'Super user'), ('teacher', 'Teacher'), ('editor', 'Editor'), ('student', 'Student')], default='student', max_length=50, verbose_name='Role')),
            ],
            options={
                'ordering': ['group', 'full_name'],
            },
        ),
        migrations.CreateModel(
            name='StudentGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name='Name')),
                ('admin', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='main.botuser')),
            ],
        ),
        migrations.AddField(
            model_name='botuser',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='main.studentgroup'),
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('mark', models.TextField(default='', verbose_name='Mark')),
                ('date_start', models.DateField(db_default=django.db.models.functions.datetime.Now())),
                ('date_end', models.DateField(db_default=django.db.models.expressions.CombinedExpression(django.db.models.functions.datetime.Now(), '+', models.Value(datetime.timedelta(days=120))))),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule', to='main.studentgroup')),
            ],
            options={
                'unique_together': {('name', 'group', 'date_start', 'date_end')},
            },
        ),
        migrations.CreateModel(
            name='SubjectScheduleItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_at', models.DateTimeField(default=main.models.get_default_start_time)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule', to='main.subject')),
            ],
            options={
                'ordering': ('start_at',),
            },
        ),
        migrations.CreateModel(
            name='SubjectScheduleItemMark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='', max_length=511, verbose_name='Title')),
                ('text', models.TextField(default='', verbose_name='Text')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marks', to='main.botuser')),
                ('subject_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marks', to='main.subjectscheduleitem')),
            ],
            options={
                'ordering': ['creator', 'subject_item'],
            },
        ),
        migrations.CreateModel(
            name='SubjectScheduleItemQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Order')),
                ('date_created', models.DateTimeField(default=datetime.datetime.now)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queues', to='main.botuser')),
                ('subject_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queue', to='main.subjectscheduleitem')),
            ],
            options={
                'ordering': ['order', 'date_created'],
                'unique_together': {('student', 'subject_item')},
            },
        ),
    ]
