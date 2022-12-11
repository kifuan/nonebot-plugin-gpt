import json
import uuid
import time
import asyncio
import aiohttp

from urllib.parse import urljoin
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, Union
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.log import logger

from .config import Config, gpt_config

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
)


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

    def __init__(self, config: Config):
        self._authorization = config.gpt_api_key
        self._session_token = config.gpt_session_token
        self._proxy = config.gpt_proxy
        self._api_baseurl = config.gpt_api_baseurl
        self._request_minimal_interval = config.gpt_request_minimal_interval
        self._timeout = aiohttp.ClientTimeout(total=config.gpt_timeout)
        self._last_request_time = 0
        self._contexts: dict[int, ChatbotContext] = {}

    @property
    def cooling_time(self):
        return self._last_request_time + self._request_minimal_interval - int(time.time())

    @classmethod
    async def get_instance(cls) -> 'Chatbot':
        """
        Gets chatbot instance, with refreshing the session when initializing.
        :return: the instance.
        """

        if cls._instance is not None:
            return cls._instance

        cls._instance = Chatbot(gpt_config)
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

    async def get_chat_response(self, unique_id: int, prompt: str) -> str:
        """
        Gets lines for specified id and prompt text.

        For example, by this way it will print all lines of the response from chatbot:
        >>> cb = await Chatbot.get_instance()

        :param unique_id: the unique id.
        :param prompt: the prompt text.
        :return: an async generator containing content in lines from ChatGPT.
        """
        result = ''
        try:
            async for line in self._get_chat_stream(unique_id, prompt):
                result = line
            return result.strip()
        except aiohttp.ClientResponseError as e:
            if e.status != 401:
                logger.error(e)
                return f'error {e.status}: {e.message}'
            return await self.refresh_session()
        except asyncio.TimeoutError:
            return '请求超时'

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

        self._last_request_time = int(time.time())

        async with aiohttp.ClientSession(
                raise_for_status=True,
                headers=self._headers,
                timeout=self._timeout
        ) as client:

            url = urljoin(self._api_baseurl, 'backend-api/conversation')
            async with client.post(url, proxy=self._proxy, data=data) as resp:
                async for line in resp.content:
                    try:
                        line = json.loads(line.decode('utf-8')[6:])
                        message = line['message']['content']['parts'][0]
                        ctx.conversation_id = line['conversation_id']
                        ctx.parent_id = line['message']['id']
                        yield message
                    except (IndexError, json.decoder.JSONDecodeError):
                        continue

    async def refresh_session(self) -> str:
        """
        Refreshes the token to avoid being expired.
        :return message to the user.
        """

        cookies = {
            '__Secure-next-auth.session-token': self._session_token
        }

        self._last_request_time = int(time.time())

        async with aiohttp.ClientSession(
                cookies=cookies,
                headers=self._headers,
                timeout=self._timeout
        ) as client:
            url = urljoin(self._api_baseurl, 'api/auth/session')
            async with client.get(url, proxy=self._proxy) as resp:
                try:
                    self._session_token = resp.cookies.get('__Secure-next-auth.session-token')
                    self._authorization = (await resp.json())['accessToken']
                    return '刷新成功'
                except Exception as e:
                    logger.error(e)
                    return '刷新失败，请到控制台查看报错。'
