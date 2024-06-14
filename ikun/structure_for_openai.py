from dataclasses import dataclass
from typing import Dict, Union, List


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class TextSubMessage:
    text: str
    type: str = "text"


@dataclass
class ImageSubMessage:
    image_url: Dict[str, str]
    type: str = "image"


@dataclass
class VisionChatMessage:
    role: str
    content: List[Union[TextSubMessage | ImageSubMessage]]


@dataclass
class OpenaiMessage:
    role: str
    content: Union[str | TextSubMessage]
