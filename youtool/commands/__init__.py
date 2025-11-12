from typing import List

from .base import Command
from .channel_id import ChannelId
from .channel_info import ChannelInfo
from .video_info import VideoInfo

COMMANDS: List[Command] = [ChannelId, ChannelInfo, VideoInfo]

__all__ = [
    "Command",
    "COMMANDS",
    "ChannelId",
    "ChannelInfo",
    "VideoInfo",
]
