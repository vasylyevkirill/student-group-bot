import asyncstdlib
from datetime import datetime
from asgiref.sync import sync_to_async

from aiogram import html, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from django.conf import settings

from main.models import BotUser, SubjectScheduleItem, SubjectScheduleItemMark, SubjectScheduleItemQueue
from main.filters import (
    DateFilter,
    NumberFilter,
    IsRegisteredFilter,
    IsEditorFilter,
    IsScheduleItemMarkEditingTitle,
    IsScheduleItemMarkEditingText,
)
from main.services.bot_user import get_user, get_student_group, create_user
from main.keyboards import (
    get_default_user_keyboard,
    get_editor_keyboard, get_admin_keyboard,
    get_superadmin_keyboard,
    get_keyboard_from_range,
    get_inline_keyboard_from_dict,
)
from main.services.group_actions import (
    get_day_schedule,
    aget_week_separated_schedule,
    aget_group_subjects_list,
    aget_group_subject_by_index,
    get_subject_closest_schedule,
)

router = Router()


def time_to_str(date: datetime) -> str:
    return date.strftime('%H:%M')


def date_to_str(date: datetime) -> str:
    return date.strftime('%d.%m.%y')


async def unregistered_user_handler(message: Message, user: BotUser | None = None) -> None:
    await message.answer(
        f'Привет, {html.bold(message.from_user.full_name)}!\n\n'
        'Я бот, который тебе поможет в обучении. Для начала напиши группу в которой ты учишься:'
    )


async def superadmin_user_handler(message: Message, user: BotUser | None = None) -> None:
    markup = get_superadmin_keyboard()
    await message.answer("Вы вошли в роль суперадмина", reply_markup=markup)


async def admin_user_handler(message: Message, user: BotUser | None = None) -> None:
    markup = get_admin_keyboard()
    await message.answer("Вы вошли в роль старосты", reply_markup=markup)


async def editor_user_handler(message: Message, user: BotUser | None = None) -> None:
    markup = get_editor_keyboard()
    await message.answer("Вы вошли в роль редактора", reply_markup=markup)


async def registered_user_handler(message: Message, user: BotUser | None = None) -> None:
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

    today_schedule_list = [f'{time_to_str(i.start_at)} {i.subject.name}' async for i in get_day_schedule(group)]
    if not len(today_schedule_list):
        today_schedule_list = ['В этот день пар нет',]

    await message.answer(f'Расписание на сегодня для {group.name}:\n\n' + '\n'.join(today_schedule_list))


@router.message(F.text == 'Расписание', IsRegisteredFilter())
async def week_schedule_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    schedule = await aget_week_separated_schedule(group)
    for day in schedule:
        await message.answer(
            f'Расписание на {day} для {group.name}:'
            '\n'.join([f'{time_to_str(i.start_at)} {i.subject.name}' for i in schedule[day]])
        )
    # TODO: make it in one message
    # await message.answer(f'Расписание на текущую неделю для {group.name}:\n\n' + schedule_text)


@router.message(F.text == 'Добавить ДЗ', IsEditorFilter())
async def add_subject_item_mark_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)
    subjects, count = await aget_group_subjects_list(group)

    subjects_list = [f'{i + 1}. {s.name}' async for i, s in asyncstdlib.enumerate(subjects)]

    await message.answer(
        'Выберите предмет:\n\n' + '\n'.join(subjects_list),
        reply_markup=get_keyboard_from_range(range(1, count + 1)),
    )


@router.message(NumberFilter(), IsEditorFilter())
async def number_handler(message: Message) -> None:
    index = int(message.text)
    group = await get_student_group(user=message.from_user)
    subject = await aget_group_subject_by_index(index, group)

    if not subject:
        await message.answer('Номер дисциплины вне списка.')
        return await add_subject_item_mark_handler(message)

    schedule = get_subject_closest_schedule(subject)
    schedule_items_list = [f'{date_to_str(i.start_at)} {time_to_str(i.start_at)}' async for i in schedule]
    schedule_items_ids = [i.id async for i in schedule]

    commands_dict = {
        dt: f'homework:schedule_item_id={schedule_items_ids[i]}'
        for i, dt in enumerate(schedule_items_list)
    }

    return await message.answer(
        f'{index}. {subject.name}\n\n' + '\n'.join(schedule_items_list),
        reply_markup=get_inline_keyboard_from_dict(commands_dict)
    )


@router.callback_query(lambda c: 'homework:' in c.data)
async def add_homework_callback_handler(callback: CallbackQuery):
    # homework:schedule_item_id=2
    schedule_item_id = int(callback.data.split('=')[1])
    schedule_item = SubjectScheduleItem.objects.filter(id=schedule_item_id)
    schedule_item = await schedule_item.afirst()
    user = await get_user(callback.from_user)

    await SubjectScheduleItemMark.objects.acreate(
        subject_item=schedule_item,
        creator=user,
    )

    return await callback.message.answer('Теперь напишите заголовок(например дз):')


@router.message(IsScheduleItemMarkEditingTitle())
async def edit_schedule_item_mark_title(message: Message) -> None:
    user = await get_user(message.from_user)
    editing_mark = await SubjectScheduleItemMark.objects.filter(creator=user, title='').afirst()

    editing_mark.title = message.text
    await editing_mark.asave(force_update=True)

    await message.answer('Заголовок успешно обновлен!')

    if editing_mark.text == '':
        return await message.answer('Теперь напишите текст:', reply_markup=ReplyKeyboardRemove())


@router.message(IsScheduleItemMarkEditingText())
async def edit_schedule_item_mark_text(message: Message) -> None:
    user = await get_user(message.from_user)
    editing_mark = await SubjectScheduleItemMark.objects.filter(creator=user, text='').afirst()

    editing_mark.text = message.text
    await editing_mark.asave(force_update=True)

    return await message.answer('Текст успешно обновлен!', reply_markup=ReplyKeyboardRemove())


@router.message(DateFilter(), IsEditorFilter())
async def date_handler(message: Message) -> None:
    date = datetime.strptime(message.text, '%d.%m.%Y')
    group = await get_student_group(user=message.from_user)
    schedule = get_day_schedule(group=group, date=date)

    schedule_items_list = [f'{i.subject.name} {time_to_str(i.start_at)}' async for i in schedule]
    schedule_items_ids = [i.id async for i in schedule]

    commands_dict = {
        dt: f'queue:schedule_item_id={schedule_items_ids[i]}'
        for i, dt in enumerate(schedule_items_list)
    }

    return await message.answer(
        f'{message.text}:\n\n' + '\n'.join(schedule_items_list),
        reply_markup=get_inline_keyboard_from_dict(commands_dict)
    )


async def show_subject_item_queue(message: Message, schedule_item: SubjectScheduleItem):
    queue = SubjectScheduleItemQueue.objects.select_related('student').filter(subject_item=schedule_item)

    queue_list = [
        f'{i + 1}. {r.student.full_name} @{r.student.username}' async for i, r in asyncstdlib.enumerate(queue)
    ]

    return await message.answer(
        f'{schedule_item.subject.name} {date_to_str(schedule_item.start_at)} {time_to_str(schedule_item.start_at)}\n\n'
        ' '.join(queue_list)
    )


@router.callback_query(lambda c: 'queue:' in c.data)
async def add_queue_callback_handler(callback: CallbackQuery):
    # queue:schedule_item_id=2
    schedule_item_id = int(callback.data.split('=')[1])
    schedule_item = SubjectScheduleItem.objects.select_related('subject').filter(id=schedule_item_id)
    schedule_item = await schedule_item.afirst()
    user = await get_user(callback.from_user)

    existing_queue_count = sync_to_async(
        SubjectScheduleItemQueue.objects.filter(student=user, subject_item=schedule_item).count
    )

    if await existing_queue_count():
        await callback.message.answer('Эта очередь уже существует очередь.')
        await show_subject_item_queue(callback.message, schedule_item)
    else:
        await SubjectScheduleItemQueue.objects.acreate(
            student=user,
            subject_item=schedule_item,
        )
        await callback.message.answer('Очередь успешно добавлена!')

    return await reply_default_user_message(callback.message, user)


@router.message(F.text == 'Создать очередь', IsEditorFilter())
async def add_queue_handler(message: Message) -> None:
    return await message.answer('Напишите дату в формате 29.09.2024:')


@router.message(F.text == 'Добавить предмет', IsEditorFilter())
@router.message(F.text == 'Управление группой', IsEditorFilter())
async def under_construction(message: Message) -> None:
    await message.answer(
        'Эта команда ещё в разработке.\n\n'
        f'Если срочно нужно разработать, пишите {settings.CUSTOMER_SUPPORT}.'
    )


@router.message(CommandStart())
async def reply_default_user_message(message: Message, user: BotUser | None = None) -> None:
    if not user:
        user = await get_user(message.from_user)
    handler_function = None
    if not user:
        handler_function = unregistered_user_handler
    elif user.role == BotUser.BotUserRoles.SUPER_USER:
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

    await reply_default_user_message(message, user)
