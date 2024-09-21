from asgiref.sync import sync_to_async

from aiogram import Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.types import Message

from main.models import BotUser, StudentGroup

# Bot token can be obtained via https://t.me/BotFather

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f'''Привет, {html.bold(message.from_user.full_name)}!\n\nЯ бот, который тебе поможет в обучении. Для начала напиши группу в которой ты учишься:''')


@dp.message()
async def message_handler(message: Message) -> None:
    user = BotUser.objects.filter(
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )
    get_user_count = sync_to_async(user.count)
    user_count = await get_user_count()
    await message.answer(f'`{message.from_user.full_name} {message.from_user.username} {user_count}`')
    if not user_count:
        group = StudentGroup.objects.filter(name=message.text)
        get_group_count = sync_to_async(group.count)
        group_count = await get_group_count()
        if not group_count:
            return await message.answer('К сожалению такой группы ещё нет. Если вы хотите добавить этого бота в свою группу, пишите: @boyegorka.')
        group = await group.afirst()
        user = await BotUser.objects.acreate(
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            telegram_id=message.from_user.id,
            group=group
        )
        await message.answer('Поздравляю! Вы успешно прошли регистрацию!')
    else:
        user = await user.afirst()
        await message.answer(f'Ты крут! Дождись конца разработки.\n\n{user}')
