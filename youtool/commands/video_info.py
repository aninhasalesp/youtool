import re
from pathlib import Path
from typing import List, Self

from youtool import YouTube

from .base import Command

YOUTUBE_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class VideoInfo(Command):
    """Get video info from a list of IDs, URLs, or CSV files, generate CSV output."""

    name = "video-info"
    arguments = [
        {
            "name": "video_references",
            "type": str,
            "nargs": "+",
            "help": "Video IDs, URLs, or CSV files containing them",
        },
        {"name": "--output", "short": "-o", "type": Path, "help": "Output CSV file path"},
    ]
    INFO_COLUMNS: List[str] = [
        "id",
        "title",
        "description",
        "published_at",
        "view_count",
        "like_count",
        "comment_count",
    ]

    @classmethod
    def execute(cls: Self, **kwargs) -> str:
        """Execute the video-info command to fetch YouTube video information from IDs, URLs, or CSV files and save them to a CSV file.
        Args:
            video_references (list[str]): List of YouTube video IDs, URLs, or CSV file paths.
            output (Path, optional): Path to the output CSV file where video information will be saved.
            api_key (str): The API key to authenticate with the YouTube Data API.
        Returns:
            str: A message indicating the result of the command. If output is specified,
                 the message will include the path to the generated CSV file. Otherwise, it will return the result as a string.
        """
        video_references: List[str] = kwargs.get("video_references", [])
        output: Path | None = kwargs.get("output")
        api_key: str = kwargs.get("api_key")

        video_ids: List[str] = []

        for ref in video_references:
            if ref.startswith("http"):
                vid_id = cls.video_id_from_url(ref)
                if vid_id:
                    video_ids.append(vid_id)
            elif YOUTUBE_VIDEO_ID_RE.match(ref):
                video_ids.append(ref)
            else:
                path = Path(ref)
                if not path.is_file():
                    raise Exception(f"Invalid file path: {ref}")
                video_ids += cls.data_from_csv(path, data_column_name="video_id")
                # vid_ids += cls.data_from_csv(path, data_column_name="video_url")

        youtube = YouTube([api_key], disable_ipv6=True)

        if not video_ids:
            raise Exception("At least one video ID, URL, or CSV file must be provided")

        # Remove duplicados e Nones
        video_ids = list(set([vid for vid in sum(video_ids, []) if vid]))

        youtube = YouTube([api_key], disable_ipv6=True)
        videos_infos = list(youtube.videos_infos(video_ids))

        return cls.data_to_csv(
            data=[cls.filter_fields(video_info, cls.INFO_COLUMNS) for video_info in videos_infos],
            output=output,
        )
