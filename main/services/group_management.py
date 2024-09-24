import datetime

from main.models import (
    Subject, BotUser, StudentGroup, SubjectScheduleItem,
    SubjectScheduleItemMark, SubjectScheduleItemQueue
)


MONTHS_LIST = 'Январь Февраль Март Апрель Май Июнь Июль Август Сентябрь Октябрь Ноябрь Декабрь'.split()
WEEK_DAYS_LIST = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()


def _get_week_day_number(week: str) -> int:
    return next(i for i, w in enumerate(WEEK_DAYS_LIST) if w in week)


def _get_month_number(month: str) -> str:
    month_number = next(i + 1 for i, m in enumerate(MONTHS_LIST) if month in m)
    if month_number > 9:
        return str(month_number)
    return f'0{month_number}'


def _parse_interval(inteval: str) -> list[str]:
    try:
        return inteval.split(' - ')
    except Exception as err:
        print(err)
        raise ValueError(f'parse_date_interval: get unexpected argument {inteval}')


def parse_time_interval(time_interval: str) -> tuple[datetime.datetime, datetime.datetime]:
    (time_start, time_end) = _parse_interval(time_interval)

    time_start, time_end = (datetime.datetime.strptime(d, '%H:%M') for d in (time_start, time_end))

    return time_start, time_end


def parse_date_interval(date_interval: str) -> tuple[datetime.datetime, datetime.datetime]:
    current_year = datetime.datetime.now().year
    (date_start, date_end) = _parse_interval(date_interval)

    # Исходный формат: "02 Сен - 12 Янв"
    date_start, date_end = (d.split() for d in (date_start, date_end))
    # Получаем формат : 02 09 2024...
    date_start, date_end = (f'{d[0]} {_get_month_number(d[1])} {current_year}' for d in (date_start, date_end))
    # В итоге парсим нашу строку
    date_start, date_end = (datetime.datetime.strptime(d, '%d %m %Y') for d in (date_start, date_end))

    if date_end < date_start:
        date_end = date_end.replace(year=current_year + 1)

    return date_start, date_end


def generate_subject_schedule(subject: Subject, day_of_the_week: str, time_interval: str) -> None:
    time_start, _ = parse_time_interval(time_interval)
    week_day_number = _get_week_day_number(day_of_the_week)
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


def create_subject_item_mark(mark: str, subject_item: SubjectScheduleItem) -> SubjectScheduleItemMark:
    return SubjectScheduleItemMark.objects.acreate(
        mark=mark,
        subject_item=subject_item
    )


def create_subject_item_queue(student: BotUser, subject_item: SubjectScheduleItem) -> SubjectScheduleItemQueue:
    return SubjectScheduleItemQueue.objects.creaete(student=student, subject_item=subject_item)
