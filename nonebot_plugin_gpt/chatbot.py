from functools import lru_cache
from revChatGPT.revChatGPT import Chatbot

from .config import gpt_config


@lru_cache
def get_chatbot() -> Chatbot:
    cb = Chatbot({
        'Authorization': gpt_config.gpt_session_token,
        'session_token': gpt_config.gpt_session_token,
    })

    cb.reset_chat()
    cb.refresh_session()

    return cb
