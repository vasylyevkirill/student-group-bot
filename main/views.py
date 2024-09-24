from aiogram import html, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from django.conf import settings

from main.models import BotUser
from main.filters import IsRegisteredFilter
from main.keyboards import get_default_user_keyboard, get_editor_keyboard, get_admin_keyboard, get_superadmin_keyboard
from main.services.bot_user import get_user, get_student_group, create_user


router = Router()


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


@router.message(F.text == 'Расписание', IsRegisteredFilter())
@router.message(F.text == 'Расписание на сегодня', IsRegisteredFilter())
async def under_construction(message: Message) -> None:
    await message.answer(f'Эта команда ещё не готова.\n\nЕсли срочно нужно разработать, пишите {settings.CUSTOMER_SUPPORT}.')


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f'''Привет, {html.bold(message.from_user.full_name)}!\n\nЯ бот, который тебе поможет в обучении. Для начала напиши группу в которой ты учишься:''')


@router.message()
async def message_handler(message: Message) -> None:
    user = await get_user(message.from_user)
    if not user:
        group = await get_student_group(message.text)
        if not group:
            return await message.answer(f'К сожалению такой группы ещё нет. Если вы хотите добавить этого бота в свою группу, пишите: {settings.CUSTOMER_SUPPORT}.')
        user = await create_user(message.from_user, group)
        await message.answer('Поздравляю! Вы успешно прошли регистрацию!')
    else:
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
