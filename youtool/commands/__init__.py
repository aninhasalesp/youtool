from typing import List

from .base import Command
from .channel_id import ChannelId
from .channel_info import ChannelInfo
from .video_info import VideoInfo
from .video_search import VideoSearch

COMMANDS: List[Command] = [ChannelId, ChannelInfo, VideoInfo, VideoSearch]

__all__ = [
    "Command",
    "COMMANDS",
    "ChannelId",
    "ChannelInfo",
    "VideoInfo",
    "VideoSearch",
]
