from datetime import datetime, timedelta


MONTHS_LIST = 'Январь Февраль Март Апрель Май Июнь Июль Август Сентябрь Октябрь Ноябрь Декабрь'.split()
WEEK_DAYS_LIST = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()


def time_to_str(date: datetime) -> str:
    return date.strftime('%H:%M')


def date_to_str(date: datetime) -> str:
    return date.strftime('%d.%m.%y')


def get_text_week_day_number(week: str) -> int:
    return next(i for i, w in enumerate(WEEK_DAYS_LIST) if w in week)


def get_text_month_number(month: str) -> str:
    month_number = next(i + 1 for i, m in enumerate(MONTHS_LIST) if month in m)
    if month_number > 9:
        return str(month_number)
    return f'0{month_number}'


def _get_datetime_start_end(
    date: datetime,
    delta_to_start: timedelta,
    delta_to_end: timedelta
) -> tuple[datetime, datetime]:
    date_start = datetime(date.year, date.month, date.day) - delta_to_start
    date_end = datetime(date.year, date.month, date.day) + delta_to_end

    return date_start, date_end


def get_day_start_end(date: datetime) -> tuple[datetime, datetime]:
    return _get_datetime_start_end(date, timedelta(), timedelta(days=1))


def get_week_start_end(date: datetime) -> tuple[datetime, datetime]:
    return _get_datetime_start_end(date, timedelta(days=date.weekday()), timedelta(days=7))


def _parse_interval(inteval: str) -> list[str]:
    try:
        return inteval.split(' - ')
    except Exception as err:
        print(err)
        raise ValueError(f'parse_date_interval: get unexpected argument {inteval}')


def parse_time_interval(time_interval: str) -> tuple[datetime, datetime]:
    (time_start, time_end) = _parse_interval(time_interval)

    time_start, time_end = (datetime.strptime(d, '%H:%M') for d in (time_start, time_end))

    return time_start, time_end


def parse_date_interval(date_interval: str) -> tuple[datetime, datetime]:
    current_year = datetime.now().year
    (date_start, date_end) = _parse_interval(date_interval)

    # Исходный формат: "02 Сен - 12 Янв"
    date_start, date_end = (d.split() for d in (date_start, date_end))
    # Получаем формат : 02 09 2024...
    date_start, date_end = (f'{d[0]} {get_text_month_number(d[1])} {current_year}' for d in (date_start, date_end))
    # В итоге парсим нашу строку
    date_start, date_end = (datetime.strptime(d, '%d %m %Y') for d in (date_start, date_end))

    if date_end < date_start:
        date_end = date_end.replace(year=current_year + 1)

    return date_start, date_end
