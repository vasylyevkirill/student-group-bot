from datetime import datetime
import itertools
from collections.abc import Iterable
from asgiref.sync import sync_to_async
from django.db.models.query import QuerySet

from main.models import StudentGroup, SubjectScheduleItem, Subject, SubjectScheduleItemMark, SubjectScheduleItemQueue
from main.helpers import get_day_start_end, get_week_start_end


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
    now = datetime.now()
    return subject.schedule.filter(start_at__gte=now)[:5]


def get_day_schedule(group: StudentGroup, date: datetime | None = None) -> QuerySet[SubjectScheduleItem]:
    if not date:
        date = datetime.now()

    date_start, date_end = get_day_start_end(date)

    return SubjectScheduleItem.objects.select_related('subject').filter(
        subject__group=group,
        start_at__gte=date_start,
        start_at__lte=date_end,
    )


def get_week_separated_schedule(
    group: StudentGroup, week_day: datetime | None = None
) -> dict[str, list[SubjectScheduleItem]]:
    if not week_day:
        week_day = datetime.now()
    week_start, week_end = get_week_start_end(week_day)

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


def get_marks_schedule(
    group: StudentGroup | None = None, date: datetime | None = None, date_schedule: Iterable | None = None
) -> dict[SubjectScheduleItem, list[SubjectScheduleItemMark]] | None:
    if not date_schedule and not date and not group:
        raise ValueError(__name__ + ': requires at least one arguments.')

    if not date_schedule:
        date_schedule = tuple(get_day_schedule(group, date))

    marks_schedule = {key: list(key.marks.all()) for key in date_schedule if key.marks.count()}

    return marks_schedule


def get_queue_schedule(
    group: StudentGroup, date: datetime | None = None
) -> dict[SubjectScheduleItem, list[SubjectScheduleItemQueue]] | None:
    pass


aget_marks_schedule = sync_to_async(get_marks_schedule)
aget_group_subjects_list = sync_to_async(get_group_subjects_list)
aget_group_subject_by_index = sync_to_async(get_group_subject_by_index)
aget_week_separated_schedule = sync_to_async(get_week_separated_schedule)
