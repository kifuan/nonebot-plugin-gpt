import random

from nonebot import on_command, on_regex, get_driver
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from typing import Union

from .chatbot import Chatbot, get_unique_id
from .config import gpt_config


driver = get_driver()
gpt = on_command('gpt')
control = on_command('gpt_control')
message = on_regex('^(?!/gpt)')


def remove_text_prefix(text: str) -> str:
    fragments = text.split(' ')
    if len(fragments) == 0:
        return text.strip()
    return text[len(fragments[0]):].strip()


@driver.on_startup
async def startup():
    # Initialize the bot.
    await Chatbot.get_instance()


@gpt.handle()
async def handle_explicit_message(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    cb = await Chatbot.get_instance()
    text = remove_text_prefix(event.get_message().extract_plain_text())

    unique_id = get_unique_id(event)
    async for line in cb.get_chat_lines(unique_id, text):
        await gpt.send(line)


@control.handle()
async def handle_control_message(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if event.sender.user_id not in gpt_config.gpt_sudoers:
        await control.send('没有权限')
        return

    text = remove_text_prefix(event.get_message().extract_plain_text())

    cb = await Chatbot.get_instance()

    if text == 'refresh_session':
        await cb.refresh_session()
        await control.send('刷新成功')
        return

    if text == 'reset_context':
        unique_id = get_unique_id(event)
        real_id = unique_id // 10
        cb.reset_or_create_context(get_unique_id(event))
        await control.send(f'重置{real_id}的上下文成功')
        return

    await control.send('无效命令')


@message.handle()
async def handle_probability_message(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if random.random() >= gpt_config.gpt_probability:
        return

    msg = event.get_message().extract_plain_text().strip()

    # Don't reply to empty messages.
    if msg == '':
        return

    cb = await Chatbot.get_instance()
    unique_id = get_unique_id(event)
    async for line in cb.get_chat_lines(unique_id, msg):
        await message.send(line)
