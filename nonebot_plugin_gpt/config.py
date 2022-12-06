from nonebot import get_driver
from pydantic import BaseModel, Extra
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    gpt_session_token: Optional[str]
    gpt_api_key: Optional[str]


gpt_config: Config = Config.parse_obj(get_driver().config)
