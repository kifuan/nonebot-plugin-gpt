import aiohttp
import json
import uuid
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, NoReturn
from .config import gpt_config

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
)


class ChatbotGroupStatus(BaseModel):
    """
    It makes the contexts independent for different groups.
    """

    conversation_id: Optional[str] = None
    parent_id: str = ''

    def reset(self):
        self.conversation_id = None
        self.parent_id = str(uuid.uuid4())


class Chatbot:
    """
    The chatbot to interact with ChatGPT.

    You should use `Chatbot.get_instance` to get the chatbot object,
    as it will refresh the session token by default.

    >>> await Chatbot.get_instance()
    """

    _instance: Optional['Chatbot'] = None

    def __init__(self):
        self.authorization = gpt_config.gpt_api_key
        self.session_token = gpt_config.gpt_session_token
        self.groups: dict[int, ChatbotGroupStatus] = {}

    @classmethod
    async def get_instance(cls) -> 'Chatbot':
        """
        Gets chatbot instance.
        :return: the instance.
        """

        if cls._instance is not None:
            return cls._instance

        cls._instance = Chatbot()
        await cls._instance.refresh_session()
        return cls._instance

    def reset_or_create_status(self, group_id: int) -> NoReturn:
        """
        Resets the status for specified group, or create a new one if not exist.
        :param group_id: the group id.
        """

        self.groups.setdefault(group_id, ChatbotGroupStatus())
        self.groups[group_id].reset()

    def get_or_create_status(self, group_id: int) -> ChatbotGroupStatus:
        """
        Gets the status for specified group, or create a new one if not exist.
        :param group_id: the group id.
        :return: the status.
        """
        self.groups.setdefault(group_id, ChatbotGroupStatus())
        return self.groups[group_id]

    @property
    def _headers(self) -> dict[str, str]:
        return {
            'Accept': 'application/json',
            'Authorization': self.authorization,
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
        }

    async def get_chat_lines(self, group_id: int, prompt: str) -> AsyncGenerator[str, None]:
        """
        Gets lines for specified group and prompt text.
        :param group_id: the group id.
        :param prompt: the prompt text.
        :return: an async generator containing content in lines from ChatGPT.
        """
        cached_line = ''
        skip = 0
        async for line in self._get_chat_stream(group_id, prompt):
            cached_line = line[skip:]
            if cached_line.endswith('\n'):
                skip += len(cached_line)
                yield cached_line.strip()

        if cached_line != '':
            yield cached_line.strip()

    async def _get_chat_stream(self, group_id: int, prompt: str) -> AsyncGenerator[str, None]:
        status = self.get_or_create_status(group_id)
        data = json.dumps({
            'action': 'next',
            'messages': [
                {
                    'id': str(uuid.uuid4()),
                    'role': 'user',
                    'content': {
                        'content_type': 'text',
                        'parts': [prompt]
                    }
                }
            ],
            'conversation_id': status.conversation_id,
            'parent_message_id': status.parent_id,
            'model': 'text-davinci-002-render'
        })

        async with aiohttp.ClientSession(raise_for_status=True, headers=self._headers) as client:
            async with client.post('https://chat.openai.com/backend-api/conversation', data=data) as resp:
                async for line in resp.content:
                    try:
                        line = json.loads(line.decode('utf-8')[6:])
                        message = line['message']['content']['parts'][0]
                        status.conversation_id = line['conversation_id']
                        status.parent_id = line['message']['id']
                        yield message
                    except (IndexError, json.decoder.JSONDecodeError):
                        continue

    async def refresh_session(self) -> NoReturn:
        """
        Refreshes the token to avoid being expired.
        """

        cookies = {
            '__Secure-next-auth.session-token': self.session_token
        }

        async with aiohttp.ClientSession(cookies=cookies, headers=self._headers) as client:
            async with client.get('https://chat.openai.com/api/auth/session') as resp:
                self.session_token = resp.cookies.get('__Secure-next-auth.session-token')
                self.authorization = (await resp.json())['accessToken']
