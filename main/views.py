import asyncstdlib
from datetime import datetime
from aiogram import html, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from django.conf import settings

from main.models import BotUser
from main.filters import IsRegisteredFilter, IsEditorFilter, DateFilter, NumberFilter
from main.services.bot_user import get_user, get_student_group, create_user
from main.keyboards import (
    get_default_user_keyboard,
    get_editor_keyboard, get_admin_keyboard,
    get_superadmin_keyboard,
    get_keyboard_from_range
)
from main.services.group_actions import (
    get_today_schedule,
    aget_week_separated_schedule,
    aget_group_subjects_list,
    aget_group_subject_by_index,
    get_subject_closest_schedule
)


router = Router()


def time_to_str(date: datetime) -> str:
    return date.strftime('%H:%M')


def date_to_str(date: datetime) -> str:
    return date.strftime('%d.%m.%y')


async def superadmin_user_handler(message: Message, user: BotUser) -> None:
    markup = get_superadmin_keyboard()
    await message.answer("Вы вошли в роль суперадмина", reply_markup=markup)


async def admin_user_handler(message: Message, user: BotUser) -> None:
    markup = get_admin_keyboard()
    await message.answer("Вы вошли в роль старосты", reply_markup=markup)


async def editor_user_handler(message: Message, user: BotUser) -> None:
    markup = get_editor_keyboard()
    await message.answer("Вы вошли в роль редактора", reply_markup=markup)


async def registered_user_handler(message: Message, user: BotUser) -> None:
    markup = get_default_user_keyboard()
    await message.answer("Вы вошли в роль студента", reply_markup=markup)


@router.message(F.text == 'Моя группа', IsRegisteredFilter())
async def my_group_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)
    if group is None:
        return await message.answer('Вы пока не прикреплены ни к какой группе.\n\nНапиши группу в которой ты учишься: ')

    admin = await get_user(user_id=group.admin_id)
    admin_text = 'к сожалению, мы ещё не успели определить старосту вашей группы.'
    if admin:
        admin_text = f'{admin.full_name} @{admin.username}'
    await message.answer(f'Ваша группа: {group.name}\n\nВаш староста: ' + admin_text)


@router.message(F.text == 'Список группы', IsRegisteredFilter())
async def my_group_list_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)
    students_list = [f'{s.full_name} @{s.username}' async for s in group.students.all()]

    await message.answer(f'Список группы {group.name}:\n\n' + '\n'.join(students_list))


@router.message(F.text == 'Расписание на сегодня', IsRegisteredFilter())
async def today_schedule_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    today_schedule_list = [f'{time_to_str(i.start_at)} {i.subject.name}' async for i in get_today_schedule(group)]

    await message.answer(f'Расписание на сегодня для {group.name}:\n\n' + '\n'.join(today_schedule_list))


@router.message(F.text == 'Расписание', IsRegisteredFilter())
async def week_schedule_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    schedule_text = ''
    schedule = await aget_week_separated_schedule(group)
    for day in schedule:
        schedule_text += f'{day}:'
        schedule_text += '\n'.join([f'{time_to_str(i.start_at)} {i.subject.name}' for i in schedule[day]])

    await message.answer(f'Расписание на сегодня для {group.name}:\n\n' + schedule_text)


@router.message(F.text == 'Добавить ДЗ', IsEditorFilter())
async def add_subject_item_mark_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)
    subjects, count = await aget_group_subjects_list(group)

    subjects_list = [f'{i + 1}. {s.name}' async for i, s in asyncstdlib.enumerate(subjects)]
    markup = get_keyboard_from_range(range(1, count + 1))

    await message.answer('Выберите предмет:\n\n' + '\n'.join(subjects_list), reply_markup=markup)


@router.message(NumberFilter(), IsEditorFilter())
async def number_handler(message: Message) -> None:
    index = int(message.text)
    group = await get_student_group(user=message.from_user)
    subject = await aget_group_subject_by_index(index, group)

    if not subject:
        await message.answer('Номер дисциплины вне списка:')
        return await add_subject_item_mark_handler(message)

    schedule = get_subject_closest_schedule(subject)
    subjects_list = [f'{date_to_str(i.start_at)} {time_to_str(i.start_at)}' async for i in schedule]

    return await message.answer(f'{index}. {subject.name}' + '\n'.join(subjects_list))


@router.message(DateFilter())
async def date_handler(message: Message) -> None:
    return await message.answer('Поздравляю, вы правильно ввели дату:')


@router.message(F.text == 'Добавить очередь', IsEditorFilter())
async def add_queue_handler(message: Message) -> None:
    return await message.answer('Напишите дату в формате 29-09-2024:')


@router.message(F.text == 'Добавить предмет', IsEditorFilter())
async def under_construction(message: Message) -> None:
    await message.answer(
        'Эта команда ещё в разработке.\n\n'
        f'Если срочно нужно разработать, пишите {settings.CUSTOMER_SUPPORT}.'
    )


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f'Привет, {html.bold(message.from_user.full_name)}!\n\n'
        'Я бот, который тебе поможет в обучении. Для начала напиши группу в которой ты учишься:'
    )


@router.message()
async def message_handler(message: Message) -> None:
    user = await get_user(message.from_user)
    if not user:
        group = await get_student_group(message.text)
        if not group:
            return await message.answer(
                'К сожалению такой группы ещё нет.\n\n'
                f'Если вы хотите добавить этого бота в свою группу, пишите: {settings.CUSTOMER_SUPPORT}.'
            )
        user = await create_user(message.from_user, group)
        await message.answer('Поздравляю! Вы успешно прошли регистрацию!')

    handler_function = None
    if user.role == BotUser.BotUserRoles.SUPER_USER:
        handler_function = superadmin_user_handler
    elif await user.ais_admin:
        handler_function = admin_user_handler
    elif user.role == BotUser.BotUserRoles.EDITOR:
        handler_function = editor_user_handler
    elif user.role == BotUser.BotUserRoles.STUDENT:
        handler_function = registered_user_handler
    else:
        return await message.answer(f'Возникла ошибка.\n\nОбратитесь к {settings.CONSTRUCTION_SUPPORT}.\n\n')

    return await handler_function(message, user)
