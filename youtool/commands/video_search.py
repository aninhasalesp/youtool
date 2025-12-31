import re
from pathlib import Path
from typing import List, Self

from youtool import YouTube

from .base import Command

YOUTUBE_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class VideoSearch(Command):
    """Search video info from IDs, URLs, or CSV files and generate CSV output."""

    name = "video-search"
    arguments = [
        {
            "name": "video_references",
            "type": str,
            "nargs": "+",
            "help": "Video IDs, URLs, or CSV files",
        },
        {"name": "--output", "short": "-o", "type": Path, "help": "Output CSV file path"},
        {"name": "--full-info", "action": "store_true", "default": False},
    ]

    INFO_COLUMNS: List[str] = ["id", "title", "published_at", "views"]
    FULL_INFO_COLUMNS: List[str] = INFO_COLUMNS + [
        "description",
        "like_count",
        "comment_count",
    ]

    @classmethod
    def execute(cls: Self, **kwargs) -> str:
        video_references: List[str] = kwargs.get("video_references", [])
        output: Path | None = kwargs.get("output")
        full_info: bool = kwargs.get("full_info", False)
        api_key: str = kwargs.get("api_key")

        info_columns = cls.FULL_INFO_COLUMNS if full_info else cls.INFO_COLUMNS

        video_ids: List[str] = []

        for ref in video_references:
            if ref.startswith("http"):
                vid = cls.video_id_from_url(ref)
                if vid:
                    video_ids.append(vid)

            elif YOUTUBE_VIDEO_ID_RE.match(ref):
                video_ids.append(ref)

            else:
                path = Path(ref)
                if not path.is_file():
                    raise Exception(f"Invalid file path: {ref}")

                video_ids += cls.data_from_csv(path, "video_id")

        if not video_ids:
            raise Exception("At least one video ID, URL, or CSV file must be provided")

        # remove duplicados
        video_ids = list(set([vid for vid in sum(video_ids, []) if vid]))

        youtube = YouTube([api_key], disable_ipv6=True)
        videos_infos = list(youtube.videos_infos(video_ids))

        return cls.data_to_csv(
            data=[cls.filter_fields(video_info, info_columns) for video_info in videos_infos],
            output=output,
        )
