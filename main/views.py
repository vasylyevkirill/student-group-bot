import asyncstdlib
from datetime import datetime
from asgiref.sync import sync_to_async

from aiogram import html, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from django.conf import settings

from main.models import BotUser, StudentGroup, SubjectScheduleItem, SubjectScheduleItemMark, SubjectScheduleItemQueue
from main.filters import (
    DateFilter,
    NumberFilter,
    IsRegisteredFilter,
    IsEditorFilter,
    IsScheduleItemMarkEditingTitle,
    IsScheduleItemMarkEditingText,
)
from main.services.bot_user import get_user, get_student_group, create_user, ais_user_editor
from main.keyboards import (
    get_default_user_keyboard,
    get_editor_keyboard, get_admin_keyboard,
    get_superadmin_keyboard,
    get_keyboard_from_range,
    get_inline_keyboard_from_dict,
)
from main.services.group_actions import (
    get_day_schedule,
    aget_marks_schedule,
    aget_group_subjects_list,
    aget_group_subject_by_index,
    aget_week_separated_schedule,
    get_subject_closest_schedule,
    aget_queue_schedule,
)
from main.helpers import time_to_str, date_to_str


router = Router()


async def no_group_handler(message: Message) -> None:
    return await message.answer(
        'К сожалению такой группы ещё нет.\n\n'
        f'Если вы хотите добавить этого бота в свою группу, пишите: {settings.CUSTOMER_SUPPORT}.',
        reply_markup=ReplyKeyboardRemove()
    )


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


@router.message(F.text == 'Добавить предмет', IsEditorFilter())
@router.message(F.text == 'Управление группой', IsEditorFilter())
async def under_construction_handler(message: Message) -> None:
    await message.answer(
        'Эта команда ещё в разработке.\n\n'
        f'Если срочно нужно разработать, пишите {settings.CUSTOMER_SUPPORT}.',
    )
    return await reply_default_user_message(message)


@router.message(F.text == 'Моя группа', IsRegisteredFilter())
async def my_group_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)
    if not group:
        return await no_group_handler(message)
    admin = await get_user(user_id=group.admin_id)
    admin_text = 'к сожалению, мы ещё не успели определить старосту вашей группы.'
    students_list = [str(s) async for s in group.students.all()]
    if admin:
        admin_text = str(admin)
    await message.answer(f'Список группы {group.name}:\n\n' + '\n'.join(students_list) + '\n\nВаш староста: ' + admin_text)


@router.message(F.text == 'Расписание на сегодня', IsRegisteredFilter())
async def today_schedule_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    today_schedule_list = [str(i) async for i in get_day_schedule(group)]
    if not len(today_schedule_list):
        today_schedule_list = ['В этот день пар нет',]

    await message.answer(f'Расписание на сегодня для {group.name}:\n\n' + '\n'.join(today_schedule_list))


@router.message(F.text == 'Расписание', IsRegisteredFilter())
async def week_schedule_handler(message: Message) -> None:
    group = await get_student_group(user=message.from_user)
    if not group:
        return await no_group_handler(message)

    schedule = await aget_week_separated_schedule(group)
    for day in schedule:
        if not schedule[day]:
            continue

        day_schedule_items = [str(i) for i in schedule[day]]
        await message.answer(
            f'Расписание на {day} для {group.name}:\n' + '\n'.join(day_schedule_items)
        )


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
        dt: f'create_homework:schedule_item_id={schedule_items_ids[i]}'
        for i, dt in enumerate(schedule_items_list)
    }

    return await message.answer(
        f'{index}. {subject.name}\n\n' + '\n'.join(schedule_items_list),
        reply_markup=get_inline_keyboard_from_dict(commands_dict)
    )


async def broadcast_schedule_item_mark(group: StudentGroup, mark: SubjectScheduleItemMark):
    from main.bot import bot

    broadcast_list = group.students.all()
    mark.subject_item

    async for student in broadcast_list:
        await bot.send_message(chat_id=student.telegram_id, text='Добавлено новое задание:\n\n' + str(mark.subject_item) + '\n\n' + str(mark))


@router.callback_query(lambda c: 'create_homework:' in c.data)
async def add_mark_callback_handler(callback: CallbackQuery) -> None:
    # homework:schedule_item_id=2
    schedule_item_id = int(callback.data.split('=')[1])
    schedule_item = SubjectScheduleItem.objects.filter(id=schedule_item_id)
    schedule_item = await schedule_item.afirst()
    user = await get_user(callback.from_user)

    await SubjectScheduleItemMark.objects.acreate(
        subject_item=schedule_item,
        creator=user,
    )

    return await callback.message.answer('Теперь напишите заголовок(например дз):', reply_markup=ReplyKeyboardRemove())


@router.message(IsScheduleItemMarkEditingTitle())
async def edit_schedule_item_mark_title(message: Message) -> None:
    user = await get_user(message.from_user)
    editing_mark = await SubjectScheduleItemMark.objects.filter(creator=user, title='').afirst()

    editing_mark.title = message.text
    await editing_mark.asave(force_update=True)

    await message.answer('Заголовок успешно обновлен!')

    if editing_mark.text == '':
        return await message.answer('Теперь напишите текст:', reply_markup=ReplyKeyboardRemove())
    else:
        return await reply_default_user_message(message, user)


@router.message(IsScheduleItemMarkEditingText())
async def edit_schedule_item_mark_text(message: Message) -> None:
    user = await get_user(message.from_user)
    group = await get_student_group(user=message.from_user)
    editing_mark = await SubjectScheduleItemMark.objects.select_related('subject_item', 'subject_item__subject').filter(creator=user, text='').afirst()

    editing_mark.text = message.text
    await editing_mark.asave(force_update=True)

    await message.answer('Текст успешно обновлен!', reply_markup=ReplyKeyboardRemove())
    await broadcast_schedule_item_mark(group, editing_mark)
    return await reply_default_user_message(message, user)


@router.message(DateFilter(), IsEditorFilter())
async def date_handler(message: Message) -> None:
    date = datetime.strptime(message.text, '%d.%m.%Y')
    group = await get_student_group(user=message.from_user)
    schedule = get_day_schedule(group=group, date=date)

    schedule_items_list = [f'{i}' async for i in schedule]
    schedule_items_ids = [i.id async for i in schedule]

    commands_dict = {
        dt: f'create_queue:schedule_item_id={schedule_items_ids[i]}'
        for i, dt in enumerate(schedule_items_list)
    }

    return await message.answer(
        f'{message.text}:\n\n' + '\n'.join(schedule_items_list),
        reply_markup=get_inline_keyboard_from_dict(commands_dict)
    )


async def get_subject_item_queue_text(schedule_item: SubjectScheduleItem) -> str:
    queue = SubjectScheduleItemQueue.objects.select_related('student').filter(subject_item=schedule_item)

    queue_list = [
        f'{r}' async for r in queue
    ]

    return (
        f'{schedule_item.subject.name} '
        f'{date_to_str(schedule_item.start_at)} '
        f'{time_to_str(schedule_item.start_at)}\n\n' + '\n'.join(queue_list)
    )


@router.callback_query(lambda c: 'create_queue:' in c.data)
async def create_queue_callback_handler(callback: CallbackQuery) -> None:
    # queue:schedule_item_id=2
    from main.bot import bot

    schedule_item_id = int(callback.data.split('=')[1])
    schedule_item_query = SubjectScheduleItem.objects.select_related('subject').filter(id=schedule_item_id)
    schedule_item = await schedule_item_query.afirst()
    user = await get_user(callback.from_user)

    if not user or user.group_id != schedule_item.subject.group_id:
        return

    query_set = SubjectScheduleItemQueue.objects.filter(subject_item=schedule_item)

    is_user_in_queue = sync_to_async(query_set.filter(student=user).count)

    if await is_user_in_queue():
        await bot.send_message(
            chat_id=user.telegram_id,
            text='Вы уже записаны в эту очередь:\n\n' + await get_subject_item_queue_text(schedule_item),
            reply_markup=get_inline_keyboard_from_dict({'Удалить себя из очереди' : f'delete_queue:schedule_item_id={schedule_item_id}'}),
        )
    else:
        is_schedule_exist = bool(await sync_to_async(query_set.count)())
        if not is_schedule_exist and not await ais_user_editor(user):
            return await bot.send_message(
                chat_id=user.telegram_id,
                text='Этой очереди больше нет, a для того чтобы создать новую вам нужно быть редактором.\n\nВы можете попросить старосту повысить вас.',
            )

        queue_record = await SubjectScheduleItemQueue.objects.acreate(
            student=user,
            subject_item=schedule_item,
        )

        if queue_record.order == 0:
            
            group = await get_student_group(user=callback.from_user)
            broadcast_list = group.students.all()
            async for student in broadcast_list:
                if student.id == user.id:
                    continue
                await bot.send_message(
                    chat_id=student.telegram_id,
                    text='Добавлена новая очередь:\n\n' + await get_subject_item_queue_text(schedule_item),
                    reply_markup=get_inline_keyboard_from_dict({'Записаться в очередь': callback.data}),
                )

        await bot.send_message(
            chat_id=user.telegram_id,
            text=f'Вы успешно записались в очередь:\n\n' + await get_subject_item_queue_text(schedule_item),
            reply_markup=get_inline_keyboard_from_dict({'Удалить себя из очереди' : f'delete_queue:schedule_item_id={schedule_item_id}'}),
        )

@router.callback_query(lambda c: 'delete_queue:' in c.data)
async def delete_queue_callback_handler(callback: CallbackQuery) -> None:
    from main.bot import bot

    schedule_item_id = int(callback.data.split('=')[1])
    schedule_item_query = SubjectScheduleItem.objects.select_related('subject').filter(id=schedule_item_id)
    schedule_item = await schedule_item_query.afirst()
    user = await get_user(callback.from_user)

    if not user or user.group_id != schedule_item.subject.group_id:
        return

    is_user_in_queue = sync_to_async(
        SubjectScheduleItemQueue.objects.filter(student=user, subject_item=schedule_item).count
    )

    if await is_user_in_queue():
        queue_record = await SubjectScheduleItemQueue.objects.aget(
            student=user,
            subject_item=schedule_item,
        )
        await queue_record.adelete()
        await bot.send_message(
            chat_id=user.telegram_id,
            text='Вы теперь не в очереди:\n\n' + await get_subject_item_queue_text(schedule_item),
            reply_markup=get_inline_keyboard_from_dict({'Записаться снова': f'create_queue:schedule_item_id={schedule_item_id}'})
        )
    else:
        await bot.send_message(
            chat_id=user.telegram_id,
            text='Вас нет в этой очереди:\n\n' + await get_subject_item_queue_text(schedule_item)
        )


@router.callback_query(lambda c: 'create_homework:' in c.data)
async def create_mark_callback_handler(callback: CallbackQuery) -> None:
    # homework:schedule_item_id=2
    schedule_item_id = int(callback.data.split('=')[1])
    schedule_item = SubjectScheduleItem.objects.filter(id=schedule_item_id)
    schedule_item = await schedule_item.afirst()
    user = await get_user(callback.from_user)

    await SubjectScheduleItemMark.objects.acreate(
        subject_item=schedule_item,
        creator=user,
    )

    return await callback.message.answer('Теперь напишите заголовок(например дз):', reply_markup=ReplyKeyboardRemove())


@router.message(F.text == 'Создать очередь', IsEditorFilter())
async def add_queue_handler(message: Message) -> None:
    return await message.answer(f'Напишите дату в формате {date_to_str(datetime.now(), mask="%d.%m.%Y")}:')


async def aget_marks_date_text(marks_schedule: dict[SubjectScheduleItem, list[SubjectScheduleItemMark]]) -> str:
    return '\n'.join([f'{i}:\n{"\n".join([str(m) for m in marks_schedule[i]])}' for i in marks_schedule.keys()])


async def aget_queue_date_text(queue_schedule: dict[SubjectScheduleItem, list[SubjectScheduleItemQueue]]) -> str:
    return '\n'.join([f'{i}:\n{"\n".join([str(q) for q in queue_schedule[i]])}' for i in queue_schedule.keys()])


@router.message(F.text == 'ДЗ на сегодня', IsRegisteredFilter())
async def get_today_mark_schedule(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    marks_schedule = await aget_marks_schedule(group)
    marks_schedule_text: str = await aget_marks_date_text(marks_schedule)

    if not len(marks_schedule_text):
        marks_schedule_text = 'На сегодня заданий нет, отдыхаем)'

    await message.answer('Список заданий на сегодня:\n\n' + marks_schedule_text)


@router.message(F.text == 'ДЗ на неделю', IsRegisteredFilter())
async def get_week_mark_schedule(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    response_text: str = ''

    schedule = await aget_week_separated_schedule(group)
    for day in schedule:
        if not schedule[day]:
            continue
        marks_day_schedule = await aget_marks_schedule(date_schedule=schedule[day])
        if not len(marks_day_schedule.keys()):
            continue

        response_text += f'{day}:\n{await aget_marks_date_text(marks_day_schedule)}\n\n'

    if not response_text:
        response_text = 'На эту неделю заданий нет.'

    return await message.answer(f'Задачи на неделю для {group.name}:\n\n' + response_text)


@router.message(F.text == 'Очереди на сегодня', IsRegisteredFilter())
async def get_today_queue_schedule(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    queue_schedule = await aget_queue_schedule(group)
    queue_schedule_text: str = await aget_queue_date_text(queue_schedule)

    if not len(queue_schedule_text):
        queue_schedule_text = 'На сегодня очередей нет, отдыхаем)'

    await message.answer('Список очередей на сегодня:\n\n' + queue_schedule_text)


@router.message(F.text == 'Очереди на неделю', IsRegisteredFilter())
async def get_week_queue_schedule(message: Message) -> None:
    group = await get_student_group(user=message.from_user)

    response_text: str = ''

    schedule = await aget_week_separated_schedule(group)
    for day in schedule:
        if not schedule[day]:
            continue
        queue_day_schedule = await aget_queue_schedule(date_schedule=schedule[day])
        if not len(queue_day_schedule.keys()):
            continue

        response_text += f'{day}:\n{await aget_queue_date_text(queue_day_schedule)}\n\n'

    if not response_text:
        response_text = 'На эту неделю очередей нет.'

    return await message.answer(f'Список очередей на неделю для {group.name}:\n\n' + response_text)


@router.message()
async def message_handler(message: Message) -> None:
    user = await get_user(message.from_user)
    if not user:
        group = await get_student_group(message.text)
        if not group:
            return await no_group_handler(message)

        user = await create_user(message.from_user, group)
        await message.answer('Поздравляю! Вы успешно прошли регистрацию!')

    await reply_default_user_message(message, user)
