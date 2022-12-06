from nonebot import on_command, Bot
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.log import logger
from .chatbot import get_chatbot

chat = on_command('chat')

gpt = on_command('gpt')


@chat.handle()
async def _(_: Bot, __: Matcher, event: GroupMessageEvent):
    text = event.get_message().extract_plain_text()
    logger.trace('group_id', event.group_id)
    logger.trace('text', text)
    cb = get_chatbot()
    resp = cb.get_chat_response(text, output='text')
    await chat.send(resp['message'])
