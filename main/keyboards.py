from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,
    ReplyKeyboardMarkup,
    InlineKeyboardBuilder,
    InlineKeyboardMarkup
)
from collections.abc import Iterable

from main.services.group_actions import WEEK_DAYS_LIST


def _get_markup(
    commands_list: Iterable[str], adjust: Iterable[int] = (2,),
    builder: ReplyKeyboardBuilder | InlineKeyboardBuilder | None = None,
) -> ReplyKeyboardMarkup | InlineKeyboardMarkup:
    if not builder:
        builder = ReplyKeyboardBuilder()

    [builder.button(text=c) for c in commands_list]
    builder.adjust(*adjust)

    return builder.as_markup(
        resize_keyboard=True,
        remove_keyboard=True,
        input_field_placeholder="Выберите команду:"
    )


def get_keyboard_from_range(number_list: Iterable[int]) -> ReplyKeyboardMarkup:
    return _get_markup([str(n) for n in number_list])


def get_default_user_keyboard() -> ReplyKeyboardMarkup:
    commands_list = 'Моя группа#Расписание#Расписание на сегодня#ДЗ на неделю#Очереди на сегодня#Очереди на неделю'.split('#')

    return _get_markup(commands_list)


def get_editor_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder().from_markup(get_default_user_keyboard())

    commands_list = 'Добавить предмет#Добавить ДЗ#Создать очередь'.split('#')

    return _get_markup(commands_list, builder=builder)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder().from_markup(get_editor_keyboard())

    commands_list = 'Управление группой'.split('#')

    return _get_markup(commands_list, builder=builder)


def get_superadmin_keyboard() -> ReplyKeyboardMarkup:
    return get_admin_keyboard()


def get_week_days_keyboard() -> ReplyKeyboardMarkup:
    return _get_markup(WEEK_DAYS_LIST)

#
# INLINE KEYBOARDS
#


def get_inline_keyboard_from_dict(commands_dict: dict[str, str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    [builder.button(text=k, callback_data=commands_dict[k]) for k in commands_dict]
    builder.adjust(1)

    return builder.as_markup()
