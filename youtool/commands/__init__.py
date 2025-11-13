from typing import List

from .base import Command
from .channel_id import ChannelId
from .channel_info import ChannelInfo
from .video_comments import VideoComments
from .video_info import VideoInfo
from .video_search import VideoSearch

COMMANDS: List[Command] = [ChannelId, ChannelInfo, VideoInfo, VideoSearch, VideoComments]

__all__ = [
    "Command",
    "COMMANDS",
    "ChannelId",
    "ChannelInfo",
    "VideoInfo",
    "VideoSearch",
    "VideoComments",
]
