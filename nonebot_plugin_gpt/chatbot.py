from revChatGPT.revChatGPT import Chatbot
from functools import lru_cache
from typing import Generator

from .config import gpt_config


@lru_cache
def get_chatbot() -> Chatbot:
    cb = Chatbot({
        'Authorization': gpt_config.gpt_api_key,
        'session_token': gpt_config.gpt_session_token,
    })

    cb.reset_chat()
    cb.refresh_session()

    return cb


def get_response_lines(text: str) -> Generator[str, None, None]:
    chatbot = get_chatbot()
    line = ''
    skip = 0
    for resp in chatbot.get_chat_response(text, output='stream'):
        line = resp['message'][skip:]
        if '\n' in line:
            skip += len(line)
            yield line.strip()

    # Check the line here to avoid missing the last line.
    if line != '':
        yield line.strip()
