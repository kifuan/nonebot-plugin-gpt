from nonebot import on_command, Bot
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from .chatbot import get_response_lines

chat = on_command('chat')

gpt = on_command('gpt')


@chat.handle()
async def _(_: Bot, __: Matcher, event: GroupMessageEvent):
    text = event.get_message().extract_plain_text()
    for line in get_response_lines(text):
        await chat.send(line)
