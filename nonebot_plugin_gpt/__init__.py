import random

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from .chatbot import Chatbot
from .config import gpt_config


gpt = on_command('gpt')
control = on_command('gpt_control')
message = on_message()


@gpt.handle()
async def _(event: GroupMessageEvent):
    cb = await Chatbot.get_instance()
    text = event.get_message().extract_plain_text()
    async for line in cb.get_chat_lines(event.group_id, text):
        await gpt.send(line)


@control.handle()
async def _(event: GroupMessageEvent):
    if event.sender.user_id not in gpt_config.gpt_sudoers:
        await control.send('没有权限')
        return

    text = event.get_message().extract_plain_text()
    cb = await Chatbot.get_instance()

    if text == 'refresh_session':
        await cb.refresh_session()
        await control.send('刷新成功')
        return

    if text == 'reset_status':
        cb.reset_or_create_status(event.group_id)
        await control.send('重置成功')
        return

    await control.send('无效命令')


@message.handle()
async def _(event: GroupMessageEvent):
    if random.random() >= gpt_config.gpt_probability:
        return

    msg = event.get_message().extract_plain_text().strip()

    # Don't reply to empty messages.
    if msg == '':
        return

    cb = await Chatbot.get_instance()
    async for line in cb.get_chat_lines(event.group_id, msg):
        await message.send(line)
