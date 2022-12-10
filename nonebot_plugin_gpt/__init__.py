import random

from nonebot import on_command, on_regex, get_driver
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from typing import Union, Optional

from .chatbot import Chatbot
from .config import gpt_config


driver = get_driver()
gpt = on_command('gpt')
control = on_command('gpt_control')
message = on_regex('^(?!/gpt)')


def get_unique_id_for_event(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> int:
    """
    Generate a unique id for the specified event, with one more number at the tail to avoid duplicate ids.

    To get the real id, you could floor divide it by 10.
    For example:
    >>> unique_id = get_unique_id_for_event(event)
    >>> real_id = unique_id // 10

    :param event the event to get unique id.
    """

    if event.message_type == 'group':
        return event.group_id * 10 + 1

    if event.message_type == 'private':
        return event.user_id * 10 + 2

    raise TypeError('invalid message type ' + event.message_type)


def remove_text_prefix(text: str) -> str:
    fragments = text.split(' ')
    if len(fragments) == 0:
        return text.strip()
    return text[len(fragments[0]):].strip()


async def get_response_for_event(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> Optional[str]:
    cb = await Chatbot.get_instance()

    if cb.cooling_time > 0:
        return f'冷却中，请 {cb.cooling_time} 秒后重试。'

    prompt = remove_text_prefix(event.get_message().extract_plain_text())
    if prompt == '':
        return None

    unique_id = get_unique_id_for_event(event)
    return await cb.get_chat_response(unique_id, prompt)


@driver.on_startup
async def startup():
    # Initialize the bot.
    await Chatbot.get_instance()


@gpt.handle()
async def handle_explicit_message(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if response := get_response_for_event(event) is not None:
        await gpt.send(response)


@control.handle()
async def handle_control_message(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if event.sender.user_id not in gpt_config.gpt_sudoers:
        await control.send('没有权限')
        return

    text = remove_text_prefix(event.get_message().extract_plain_text())

    cb = await Chatbot.get_instance()

    if text == 'refresh_session':
        response = await cb.refresh_session()
        await control.send(response)
        return

    if text == 'reset_context':
        unique_id = get_unique_id_for_event(event)
        real_id = unique_id // 10
        cb.reset_or_create_context(get_unique_id_for_event(event))
        await control.send(f'重置{real_id}的上下文成功')
        return

    await control.send('无效命令')


@message.handle()
async def handle_probability_message(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if response := get_response_for_event(event) is not None:
        await message.send(response)
