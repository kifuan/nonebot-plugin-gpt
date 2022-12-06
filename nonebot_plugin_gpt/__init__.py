from nonebot import on_command, Bot
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from .chatbot import Chatbot

chat = on_command('chat')

gpt = on_command('gpt')


@chat.handle()
async def _(_: Bot, __: Matcher, event: GroupMessageEvent):
    cb = await Chatbot.get_instance()
    text = event.get_message().extract_plain_text()
    async for line in cb.get_chat_lines(text):
        await chat.send(line)


@gpt.handle()
async def _(_: Bot, __: Matcher, event: GroupMessageEvent):
    text = event.get_message().extract_plain_text()
    cb = await Chatbot.get_instance()

    if text == 'refresh_session':
        await cb.refresh_session()
        await gpt.send('刷新成功')

    elif text == 'reset_status':
        cb.reset_or_create_status(event.group_id)
        await gpt.send('重置成功')

    else:
        await gpt.send('无效命令')
