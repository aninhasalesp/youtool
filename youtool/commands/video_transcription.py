from pathlib import Path
from typing import List, Self

from youtool import YouTube

from .base import Command


class VideoTranscription(Command):
    """Download video transcriptions from YouTube videos."""

    name = "video-transcription"
    arguments = [
        {
            "name": "video_reference",
            "type": str,
            "nargs": "+",
            "help": "Video IDs, URLs, or CSV files containing them",
        },
        {
            "name": "--output-dir",
            "short": "-o",
            "type": Path,
            "required": True,
            "help": "Output directory to save transcriptions",
        },
        {
            "name": "--language-code",
            "short": "-g",
            "type": str,
            "required": True,
            "help": "Language code for transcription",
        },
        {"name": "--url-column-name", "type": str, "help": "CSV column for video URLs"},
        {"name": "--id-column-name", "type": str, "help": "CSV column for video IDs"},
    ]

    ID_COLUMN_NAME = "video_id"
    URL_COLUMN_NAME = "video_url"

    @classmethod
    def execute(cls: Self, **kwargs) -> str:
        video_references: List[str] = kwargs["video_reference"]
        output_dir: Path = kwargs["output_dir"]
        language_code: str = kwargs["language_code"]
        api_key: str = kwargs["api_key"]

        url_column = kwargs.get("url_column_name") or cls.URL_COLUMN_NAME
        id_column = kwargs.get("id_column_name") or cls.ID_COLUMN_NAME

        video_ids: List[str] = []

        for ref in video_references:
            if ref.startswith("http"):
                vid = cls.video_id_from_url(ref)
                if vid:
                    video_ids.append(vid)

            elif Path(ref).is_file():
                video_ids += cls.data_from_csv(Path(ref), id_column)
                urls = cls.data_from_csv(Path(ref), url_column)
                for url in urls:
                    vid = cls.video_id_from_url(url)
                    if vid:
                        video_ids.append(vid)

            else:
                video_ids.append(ref)

        if not video_ids:
            raise Exception("At least one valid video ID or URL must be provided")

        # remove duplicados mantendo ordem
        # video_ids = list(dict.fromkeys(video_ids))

        video_ids = list(set([vid for vid in sum(video_ids, []) if vid]))

        youtube = YouTube([api_key], disable_ipv6=True)
        youtube.videos_transcriptions(video_ids, language_code, output_dir)

        saved = []
        for vid in video_ids:
            path = output_dir / f"{vid}.{language_code}.vtt"
            if path.is_file():
                saved.append(str(path))

        return "\n".join(saved)
