from nonebot import on_command
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from .chatbot import Chatbot
from .config import gpt_config


chat = on_command('chat')
gpt = on_command('chat_control')


@chat.handle()
async def _(event: GroupMessageEvent):
    cb = await Chatbot.get_instance()
    text = event.get_message().extract_plain_text()
    async for line in cb.get_chat_lines(event.group_id, text):
        await chat.send(line)


@gpt.handle()
async def _(event: GroupMessageEvent):
    if event.sender.user_id not in gpt_config.gpt_sudoers:
        await gpt.send('没有权限')
        return

    text = event.get_message().extract_plain_text()
    cb = await Chatbot.get_instance()

    if text == 'refresh_session':
        await cb.refresh_session()
        await gpt.send('刷新成功')
        return

    if text == 'reset_status':
        cb.reset_or_create_status(event.group_id)
        await gpt.send('重置成功')
        return

    await gpt.send('无效命令')
