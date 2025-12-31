from pathlib import Path
from typing import List, Self

from youtool import YouTube

from .base import Command


class VideoComments(Command):
    """
    Get comments from a video ID, generate CSV output
    """

    name = "video-comments"
    arguments = [
        {
            "name": "video_references",
            "type": str,
            "nargs": "+",
            "help": "List of video IDs or CSV file paths containing video IDs",  # pelo menos um
        },
        {"name": "--output", "short": "-o", "type": Path, "help": "Output CSV file path"},
        {"name": "--id-column-name", "short": "-i", "type": str, "help": "ID column name in CSV input files"},
    ]

    COMMENT_COLUMNS: List[str] = ["comment_id", "author_display_name", "text_display", "like_count", "published_at"]

    @classmethod
    def execute(cls: Self, **kwargs) -> str:
        """
        Execute the get-comments command to fetch comments from a YouTube video and save them to a CSV file.

        - a YouTube video ID (`--ids`).

        Args:
            video_references (list[str]): List of YouTube video IDs or CSV file paths containing video IDs.
            output (Path): Path to the output CSV file where comments will be saved.
            api_key (str): The API key to authenticate with the YouTube Data API.

        Returns:
            A message indicating the result of the command. If output is specified,
            the message will include the path to the generated CSV file.
            Otherwise, it will return the result as a string.
        """
        video_references: List[str] = kwargs.get("video_references", [])
        output = kwargs.get("output")
        api_key = kwargs.get("api_key")
        id_column_name: str = kwargs.get("id_column_name") or "video_id"

        video_ids: List[str] = []

        for ref in video_references:
            if ref.startswith("http"):
                vid_id = cls.video_id_from_url(ref)
                if vid_id:
                    video_ids.append(vid_id)
            elif len(ref) == 11 and ref.isalnum():
                video_ids.append(ref)
            else:
                video_ids += cls.data_from_csv(Path(ref), data_column_name=id_column_name)

        youtube = YouTube([api_key], disable_ipv6=True)

        all_comments = []
        for vid_id in video_ids:
            all_comments.extend(youtube.video_comments(vid_id))

        return cls.data_to_csv(data=all_comments, output=output)
