import datetime
from asgiref.sync import sync_to_async

from django.db.models.functions import Now
from django.db import models


def get_default_start_time() -> datetime.datetime:
    return datetime.datetime.now() + datetime.timedelta(days=1)


class BotUser(models.Model):
    class BotUserRoles(models.TextChoices):
        SUPER_USER = 'superuser', 'Super user'
        TEACHER = 'teacher', 'Teacher'
        EDITOR = 'editor', 'Editor'
        STUDENT = 'student', 'Student'

    full_name = models.CharField('Full name', max_length=511)
    username = models.CharField('Username', max_length=511, unique=True)
    telegram_id = models.CharField('Telegram id', max_length=511, unique=True)
    group = models.ForeignKey(
        'StudentGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='students',
    )
    role = models.CharField(
        'Role',
        max_length=50,
        choices=BotUserRoles.choices,
        default=BotUserRoles.STUDENT,
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.group:
            if self.group.admin:
                return
            self.group.admin = self
            self.group.save()

    @property
    def is_admin(self) -> bool:
        return self.group.admin == self

    @property
    @sync_to_async
    def ais_admin(self) -> bool:
        return self.is_admin

    class Meta:
        ordering = 'group full_name'.split()


class StudentGroup(models.Model):
    name = models.CharField('Name', max_length=255, unique=True)
    admin = models.ForeignKey(
        BotUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='students',
    )


class Subject(models.Model):
    name = models.CharField('Name', max_length=255)
    group = models.ForeignKey(
        StudentGroup,
        on_delete=models.CASCADE,
        blank=False,
        related_name='schedule',
    )

    mark = models.TextField('Mark', blank=False, null=False, default='')
    date_start = models.DateField(db_default=Now())
    date_end = models.DateField(db_default=Now() + datetime.timedelta(days=120))

    class Meta:
        unique_together = (('name', 'group', 'date_start', 'date_end'),)


class SubjectScheduleItem(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        blank=False,
        related_name='schedule',
    )
    start_at = models.DateTimeField(default=get_default_start_time)

    class Meta:
        ordering = ('start_at',)


class SubjectScheduleItemMark(models.Model):
    title = models.CharField('Title', max_length=511, default='')
    text = models.TextField('Text', blank=False, null=False, default='')
    creator = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        blank=False,
        related_name='marks',
    )
    subject_item = models.ForeignKey(
        SubjectScheduleItem,
        on_delete=models.CASCADE,
        blank=False,
        related_name='marks',
    )

    class Meta:
        ordering = 'creator subject_item'.split()


class SubjectScheduleItemQueue(models.Model):
    student = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        blank=False,
    )
    subject_item = models.ForeignKey(
        SubjectScheduleItem,
        on_delete=models.CASCADE,
        blank=False,
    )

    order = models.PositiveIntegerField('Order', default=0)
    date_created = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = 'order date_created'.split()
