import datetime
import itertools
from asgiref.sync import sync_to_async
from django.db.models.query import QuerySet

from main.models import StudentGroup, SubjectScheduleItem, Subject


WEEK_DAYS_LIST = 'Понедельник Вторник Среда Четверг Пятница Суббота Воскресенье'.split()


def get_group_subjects_list(group: StudentGroup) -> tuple[QuerySet, int]:
    subjects = Subject.objects.filter(group=group)
    count = subjects.count()
    return Subject.objects.filter(group=group), count


def get_group_subject_by_index(index: int, group: StudentGroup) -> Subject | None:
    queryset, _ = get_group_subjects_list(group)
    subject = next(itertools.islice(queryset, index - 1, None))
    if not isinstance(subject, Subject):
        return None
    return subject


def get_subject_closest_schedule(subject: Subject) -> QuerySet:
    now = datetime.datetime.now()
    return subject.schedule.filter(start_at__gte=now)[:5]


def get_day_schedule(group: StudentGroup, date: datetime.datetime | None = None) -> QuerySet:
    if not date:
        date = datetime.datetime.now()

    date_start = datetime.datetime(date.year, date.month, date.day)
    date_end = date_start + datetime.timedelta(days=1)

    return SubjectScheduleItem.objects.select_related('subject').filter(
        subject__group=group,
        start_at__gte=date_start,
        start_at__lte=date_end,
    )


def get_week_separated_schedule(group: StudentGroup) -> dict:
    now = datetime.datetime.now()
    week_start = datetime.datetime(now.year, now.month, now.day) - datetime.timedelta(days=now.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    week_schedule = SubjectScheduleItem.objects.select_related('subject').filter(
        subject__group=group,
        start_at__gte=week_start,
        start_at__lte=week_end,
    )

    splited_schedule = {d: [] for d in WEEK_DAYS_LIST}

    for schedule_item in week_schedule:
        week_day_number = schedule_item.start_at.weekday()

        splited_schedule[WEEK_DAYS_LIST[week_day_number]].append(schedule_item)

    return splited_schedule


aget_week_separated_schedule = sync_to_async(get_week_separated_schedule)
aget_group_subjects_list = sync_to_async(get_group_subjects_list)
aget_group_subject_by_index = sync_to_async(get_group_subject_by_index)
