"""exteraGram `extera_utils.text_formatting` on the AyuGram iOS runtime.

The text is passed through with its markup intact and the parse mode is
forwarded to the host, which parses HTML/Markdown with the app's own entity
parser when sending. `entities` is therefore empty here.
"""
import enum


class TLEntityType(enum.Enum):
    CODE = "code"
    PRE = "pre"
    STRIKETHROUGH = "strikethrough"
    TEXT_LINK = "text_link"
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    SPOILER = "spoiler"
    CUSTOM_EMOJI = "custom_emoji"
    BLOCKQUOTE = "blockquote"


class RawEntity:
    def __init__(self, type, offset, length, url=None, language=None, document_id=None, collapsed=False):
        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.language = language
        self.document_id = document_id
        self.collapsed = collapsed


def parse_text(text, parse_mode="HTML", is_caption=False):
    return {"caption" if is_caption else "message": text, "entities": [], "parse_mode": parse_mode}
