from datetime import datetime
from pathlib import Path
from typing import List, Optional, Self

from youtool import YouTube

from .base import Command


class VideoLiveChat(Command):
    """Get live chat comments from a video ID, generate CSV output (same schema for chat_message dicts)"""

    name = "video-livechat"
    arguments = [
        {"name": "--ids", "short": "-i", "type": str, "help": "Video ID", "required": True},
        {"name": "--output-file-path", "short": "-o", "type": Path, "help": "Output CSV file path"},
        {"name": "--expand-emojis", "short": "-e", "action": "store_true", "help": "Expand emojis in chat messages"},
    ]

    CHAT_COLUMNS: List[str] = [
        "id",
        "video_id",
        "created_at",
        "type",
        "action",
        "video_time",
        "author",
        "author_id",
        "author_image_url",
        "text",
        "money_currency",
        "money_amount",
    ]

    @staticmethod
    def parse_timestamp(timestamp: str) -> str:
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "")).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return timestamp

    @staticmethod
    def parse_decimal(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ""))
        except Exception:
            return None

    @classmethod
    def execute(cls: Self, **kwargs) -> str:
        """
        Execute the video-livechat command to fetch live chat messages from a YouTube video and save them to a CSV file.

        - a YouTube video ID (`--ids`).

        Args:
            ids (str): The ID of the YouTube video.
            output_file_path (Path): Path to the output CSV file where chat messages will be saved.
            expand_emojis (bool): Whether to expand emojis in chat messages. Defaults to True.
            api_key (str): The API key to authenticate with the YouTube Data API.

        Returns:
            A message indicating the result of the command. If output_file_path is specified,
            the message will include the path to the generated CSV file.
            Otherwise, it will return the result as a string.
        """
        ids = kwargs.get("ids")
        output_file_path = kwargs.get("output_file_path")
        expand_emojis = kwargs.get("expand_emojis", True)
        api_key = kwargs.get("api_key")

        youtube = YouTube([api_key], disable_ipv6=True)

        chat_messages = list(youtube.video_livechat(ids, expand_emojis))

        return cls.data_to_csv(data=chat_messages, output_file_path=output_file_path)
