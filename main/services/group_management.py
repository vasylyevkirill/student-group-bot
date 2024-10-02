import datetime

from django.db.models import Q
from main.models import (
    Subject, BotUser, StudentGroup, SubjectScheduleItem,
    SubjectScheduleItemMark, SubjectScheduleItemQueue
)
from main.helpers import (
    parse_time_interval,
    parse_date_interval,
    get_text_week_day_number,
)


def generate_subject_schedule(subject: Subject, day_of_the_week: str, time_interval: str) -> None:
    time_start, _ = parse_time_interval(time_interval)
    week_day_number = get_text_week_day_number(day_of_the_week)
    date = subject.date_start
    date += datetime.timedelta(days=7 - date.weekday() + week_day_number)
    while (subject.date_end > date):
        SubjectScheduleItem.objects.get_or_create(
            subject=subject,
            start_at=time_start.replace(year=date.year, month=date.month, day=date.day),
        )
        date += datetime.timedelta(days=7)


def create_subject(
    name: str, group: StudentGroup, mark: str,
    day_of_the_week: str, date_interval: str, time_interval: str
) -> Subject:
    date_start, date_end = parse_date_interval(date_interval)
    subject, _ = Subject.objects.get_or_create(
        name=name,
        mark=mark,
        group=group,
        date_start=date_start,
        date_end=date_end,
    )
    generate_subject_schedule(subject=subject, day_of_the_week=day_of_the_week, time_interval=time_interval)
    return subject


def get_user_editable_schedule_item_mark(user: BotUser) -> SubjectScheduleItemMark | None:
    editing_marks = SubjectScheduleItemMark.objects.filter(Q(title='') | Q(text=''), creator=user)
    if not editing_marks.count():
        return None
    return editing_marks.first()


def create_subject_item_queue(student: BotUser, subject_item: SubjectScheduleItem) -> SubjectScheduleItemQueue:
    return SubjectScheduleItemQueue.objects.creaete(student=student, subject_item=subject_item)
