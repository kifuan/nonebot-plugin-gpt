import pkgutil
import textwrap

from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
from .config import gpt_config


@lru_cache()
def _get_font() -> ImageFont.FreeTypeFont:
    user_font = gpt_config.gpt_image_font
    font = pkgutil.get_data(__name__, 'font.otf') if user_font is None else user_font
    return ImageFont.truetype(font, gpt_config.gpt_image_font_size)


def _wrap_lines(text: str) -> list[str]:
    return [
        line for raw_line in text.splitlines(True)
        for line in textwrap.wrap(raw_line, gpt_config.gpt_image_line_width, replace_whitespace=False)
    ]


def convert_text_to_image(text: str) -> bytes:
    lines = _wrap_lines(text)
    font = _get_font()
    width = max(int(font.getlength(line)) for line in lines) + 2 * gpt_config.gpt_image_padding
    height = (
            len(lines) * (gpt_config.gpt_image_font_size + gpt_config.gpt_image_padding) +
            2 * gpt_config.gpt_image_padding
    )
    image = Image.new('RGB', (width, height), (255, 255, 255))

    draw = ImageDraw.Draw(image)

    for i, line in enumerate(lines):
        top = i * (gpt_config.gpt_image_font_size + gpt_config.gpt_image_padding) + gpt_config.gpt_image_padding
        draw.text((gpt_config.gpt_image_padding, top), text=line, fill=(0, 0, 0), font=font)

    return image.tobytes()
