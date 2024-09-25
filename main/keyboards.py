from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from collections.abc import Iterable

from main.services.group_actions import WEEK_DAYS_LIST


def _get_markup(
    commands_list: Iterable[str], adjust: Iterable[int] = (2,),
    builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
) -> ReplyKeyboardMarkup:
    [builder.button(text=c) for c in commands_list]
    builder.adjust(*adjust)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите команду:"
    )


def get_default_user_keyboard() -> ReplyKeyboardMarkup:
    commands_list = 'Моя группа#Список группы#Расписание#Расписание на сегодня'.split('#')

    return _get_markup(commands_list)


def get_editor_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder().from_markup(get_default_user_keyboard())

    commands_list = 'Добавить предмет#Добавить ДЗ#Добавить очередь'.split('#')

    return _get_markup(commands_list, builder=builder)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder().from_markup(get_editor_keyboard()())

    commands_list = 'Управление группой'.split('#')

    return _get_markup(commands_list, builder=builder)


def get_superadmin_keyboard() -> ReplyKeyboardMarkup:
    return get_admin_keyboard()


def get_week_days_keyboard() -> ReplyKeyboardMarkup:
    return _get_markup(WEEK_DAYS_LIST)
