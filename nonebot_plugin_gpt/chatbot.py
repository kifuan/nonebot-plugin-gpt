import json
import uuid
import time
import asyncio
import aiohttp

from pydantic import BaseModel
from typing import AsyncGenerator, Optional, Union
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent

from .config import gpt_config

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
)


# The request interval in seconds.
REQUEST_DURATION = 5


class ChatbotContext(BaseModel):
    """
    It makes the contexts independent for different people or groups.
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

    >>> cb = await Chatbot.get_instance()
    """

    _instance: Optional['Chatbot'] = None

    def __init__(self):
        self._authorization = gpt_config.gpt_api_key
        self._session_token = gpt_config.gpt_session_token
        self._proxy = gpt_config.gpt_proxy
        self._api_baseurl = gpt_config.gpt_api_baseurl
        self._last_request_time = 0
        self._contexts: dict[int, ChatbotContext] = {}

    async def _sleep_for_next_request(self):
        now = int(time.time())
        request_should_after = self._last_request_time + REQUEST_DURATION
        if request_should_after > now:
            # Sleep for the remaining seconds.
            await asyncio.sleep(request_should_after - now)
        self._last_request_time = int(time.time())

    @classmethod
    async def get_instance(cls) -> 'Chatbot':
        """
        Gets chatbot instance, with refreshing the session when initializing.
        :return: the instance.
        """

        if cls._instance is not None:
            return cls._instance

        cls._instance = Chatbot()
        await cls._instance.refresh_session()
        return cls._instance

    def reset_or_create_context(self, unique_id: int) -> None:
        """
        Resets the context for specified id, or create a new one if not exist.
        :param unique_id: the unique id.
        """

        self._contexts.setdefault(unique_id, ChatbotContext())
        self._contexts[unique_id].reset()

    def get_or_create_context(self, unique_id: int) -> ChatbotContext:
        """
        Gets the context for specified id, or create a new one if not exist.
        :param unique_id: the unique id.
        :return: the context.
        """
        self._contexts.setdefault(unique_id, ChatbotContext())
        return self._contexts[unique_id]

    @property
    def _headers(self) -> dict[str, str]:
        # https://github.com/acheong08/ChatGPT/blob/main/src/revChatGPT/revChatGPT.py
        return {
            'Host': 'chat.openai.com',
            'Referer': 'https://chat.openai.com/chat',
            'X-Openai-Assistant-App-Id': '',
            'Connection': 'close',
            'Accept': 'text/event-stream',
            'Authorization': self._authorization,
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
        }

    async def get_chat_lines(self, unique_id: int, prompt: str) -> AsyncGenerator[str, None]:
        """
        Gets lines for specified id and prompt text.

        For example, by this way it will print all lines of the response from chatbot:
        >>> cb = await Chatbot.get_instance()
        >>> async for line in cb.get_chat_lines(unique_id, 'Hi'):
        >>>     print(line)

        :param unique_id: the unique id.
        :param prompt: the prompt text.
        :return: an async generator containing content in lines from ChatGPT.
        """
        cached_line = ''
        skip = 0

        try:
            async for full_content in self._get_chat_stream(unique_id, prompt):
                cached_line = full_content[skip:]
                if cached_line.endswith('\n'):
                    skip += len(cached_line)
                    yield cached_line.strip()
        except aiohttp.ClientResponseError as e:
            yield f'error {e.status}: {e.message}'
            return

        if cached_line != '':
            yield cached_line.strip()

    async def _get_chat_stream(self, unique_id: int, prompt: str) -> AsyncGenerator[str, None]:
        ctx = self.get_or_create_context(unique_id)
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
            'conversation_id': ctx.conversation_id,
            'parent_message_id': ctx.parent_id,
            'model': 'text-davinci-002-render'
        })

        await self._sleep_for_next_request()

        async with aiohttp.ClientSession(raise_for_status=True, headers=self._headers) as client:
            async with client.post('https://chat.openai.com/backend-api/conversation', proxy=self._proxy, data=data) as resp:
                async for line in resp.content:
                    try:
                        line = json.loads(line.decode('utf-8')[6:])
                        message = line['message']['content']['parts'][0]
                        ctx.conversation_id = line['conversation_id']
                        ctx.parent_id = line['message']['id']
                        yield message
                    except (IndexError, json.decoder.JSONDecodeError):
                        continue

    async def refresh_session(self) -> None:
        """
        Refreshes the token to avoid being expired.
        """

        cookies = {
            '__Secure-next-auth.session-token': self._session_token
        }

        await self._sleep_for_next_request()

        async with aiohttp.ClientSession(cookies=cookies, headers=self._headers) as client:
            async with client.get('https://chat.openai.com/api/auth/session', proxy=self._proxy) as resp:
                self._session_token = resp.cookies.get('__Secure-next-auth.session-token')
                self._authorization = (await resp.json())['accessToken']


def get_unique_id(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> int:
    """
    Generate a unique id for the specified event, with one more number at the tail to avoid duplicate ids.

    To get the real id, you could floor divide it by 10.
    For example:
    >>> unique_id = get_unique_id(event)
    >>> real_id = unique_id // 10

    :param event the event to get unique id.
    """

    if event.message_type == 'group':
        return event.group_id * 10 + 1

    if event.message_type == 'private':
        return event.user_id * 10 + 2

    raise TypeError('invalid message type ' + event.message_type)
