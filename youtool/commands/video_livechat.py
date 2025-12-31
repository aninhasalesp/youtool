from datetime import datetime
from pathlib import Path
from typing import List, Optional, Self

from youtool import YouTube

from .base import Command


class VideoLiveChat(Command):
    """Get live chat messages from YouTube videos."""

    name = "video-livechat"
    arguments = [
        {
            "name": "video_reference",
            "type": str,
            "nargs": "+",
            "help": "YouTube video IDs or URLs",
        },
        {"name": "--output", "short": "-o", "type": Path, "help": "Output CSV file path"},
        {
            "name": "--expand-emojis",
            "short": "-e",
            "action": "store_true",
            "help": "Expand emojis in chat messages",
        },
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
        video_references: List[str] = kwargs["video_reference"]
        output: Path | None = kwargs.get("output")
        expand_emojis: bool = kwargs.get("expand_emojis", False)
        api_key: str = kwargs["api_key"]

        video_ids: List[str] = []

        for ref in video_references:
            if ref.startswith("http"):
                vid = cls.video_id_from_url(ref)
                if vid:
                    video_ids.append(vid)
            else:
                video_ids.append(ref)

        if not video_ids:
            raise Exception("At least one valid video ID or URL must be provided")

        # remove duplicados preservando simplicidade
        video_ids = list(dict.fromkeys(video_ids))

        youtube = YouTube([api_key], disable_ipv6=True)

        chat_messages = []
        for video_id in video_ids:
            chat_messages.extend(youtube.video_livechat(video_id, expand_emojis))

        return cls.data_to_csv(data=chat_messages, output=output)
