import datetime
from asgiref.sync import sync_to_async
from django.db.models.query import QuerySet


from main.models import StudentGroup, SubjectScheduleItem


WEEK_DAYS_LIST = 'Понедельник Вторник Среда Четверг Пятница Суббота Воскресенье'.split()


def get_today_schedule(group: StudentGroup) -> QuerySet:
    now = datetime.datetime.now()
    today_start = datetime.datetime(now.year, now.month, now.day)
    today_end = today_start.replace(day=now.day + 1)

    return SubjectScheduleItem.objects.select_related('subject').filter(
        subject__group=group,
        start_at__gte=today_start,
        start_at__lte=today_end,
    )


def get_week_separated_schedule(group: StudentGroup) -> dict:
    now = datetime.datetime.now()
    week_start = datetime.datetime(now.year, now.month, now.day - now.weekday())
    week_end = week_start.replace(day=week_start.day + 6)

    week_schedule = SubjectScheduleItem.objects.select_related('subject').filter(
        subject__group=group,
        start_at__gte=week_start,
        start_at__lte=week_end,
    )

    splited_schedule = dict.fromkeys(WEEK_DAYS_LIST, [])

    for schedule_item in week_schedule:
        week_day_number = schedule_item.start_at.weekday()
        splited_schedule[WEEK_DAYS_LIST[week_day_number]].append(schedule_item)

    return splited_schedule


aget_week_separated_schedule = sync_to_async(get_week_separated_schedule)
