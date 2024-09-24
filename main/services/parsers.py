import json
import requests

from main.services.group_management import WEEK_DAYS_LIST, create_subject
from main.models import StudentGroup


def parse_mospolytech_subjects(group: StudentGroup, token: str, ):
    url = f'https://e.mospolytech.ru/old/lk_api.php/?getSchedule=&group={group.name}&token={token}'
    response = requests.get(url)
    subjects = json.loads(response.content)
    for week_day in WEEK_DAYS_LIST:
        if week_day not in subjects:
            continue
        day_subjects = subjects[week_day]['lessons']
        for subject in day_subjects:
            create_subject(
                mark='',
                group=group,
                name=subject['name'],
                day_of_the_week=week_day,
                date_interval=subject['dateInterval'],
                time_interval=subject['timeInterval'],
            )
