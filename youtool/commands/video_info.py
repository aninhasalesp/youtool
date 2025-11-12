from pathlib import Path
from typing import List, Self

from youtool import YouTube

from .base import Command


class VideoInfo(Command):
    """Get video info from a list of IDs or URLs (or CSV filename with URLs/IDs inside), generate CSV output (same schema for video dicts)")"""

    name = "video-info"
    arguments = [
        {"name": "--ids", "type": str, "help": "Video IDs", "nargs": "*", "mutually_exclusive_group": "input_source"},
        {"name": "--urls", "type": str, "help": "Video URLs", "nargs": "*", "mutually_exclusive_group": "input_source"},
        {
            "name": "--urls-file-path",
            "type": Path,
            "help": "Channels urls csv file path",
            "mutually_exclusive_group": "input_source",
        },
        {"name": "--ids-file-path", "type": Path, "help": "Channel IDs CSV file path"},
        {"name": "--output-file-path", "type": Path, "help": "Output CSV file path"},
        {"name": "--url_column_name", "type": str, "help": "URL column name on CSV input files"},
        {"name": "--id_column_name", "type": str, "help": "ID column name on CSV input files"},
        {"name": "--info_columns", "type": str, "help": "Comma-separated list of columns to include in the output CSV"},
    ]

    ID_COLUMN_NAME: str = "video_id"
    URL_COLUMN_NAME: str = "video_url"
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
        """
        Execute the video-info command to fetch YouTube video information from IDs or URLs and save them to a CSV file.

        - a list of YouTube video IDs (`--ids`), or
        - a list of YouTube video URLs (`--urls`), or
        - a CSV file containing those URLs (`--urls-file-path`) or IDs (`--ids-file-path`).

        Args:
            ids (list[str], optional): List of YouTube video IDs.
                                        Mutually exclusive with `urls` and `input_file_path`.
            urls (list[str], optional): List of YouTube video URLs.
                                        Mutually exclusive with `ids` and `input_file_path`.
            urls_file_path (Path, optional): Path to a CSV file containing YouTube video URLs.
            ids_file_path (Path, optional): Path to a CSV file containing YouTube video IDs.
            output_file_path (Path, optional): Path to the output CSV file where video information will be saved.
            api_key (str): The API key to authenticate with the YouTube Data API.
            url_column_name (str, optional): The name of the column in the input_file_path CSV file that contains the URLs.
                                            Default is "video_url".
            id_column_name (str, optional): The name of the column in the input_file_path CSV file that contains the IDs.
                                            Default is "video_id".
            info_columns (str, optional): Comma-separated list of columns to include in the output CSV.
                                            Default is the class attribute INFO_COLUMNS.

        Returns:
            str: A message indicating the result of the command. If output_file_path is specified, the message will
                include the path to the generated CSV file. Otherwise, it will return the result as a string.

        Raises:
            Exception: If neither ids, urls, nor input_file_path is provided.
        """
        ids = kwargs.get("ids") or []
        urls = kwargs.get("urls") or []
        ids_file_path = kwargs.get("ids_file_path")
        urls_file_path = kwargs.get("urls_file_path")
        output_file_path = kwargs.get("output_file_path")
        api_key = kwargs.get("api_key")

        url_column_name = kwargs.get("url_column_name") or VideoInfo.URL_COLUMN_NAME
        id_column_name = kwargs.get("id_column_name") or VideoInfo.ID_COLUMN_NAME

        info_columns = kwargs.get("info_columns")

        info_columns = (
            [column.strip() for column in info_columns.split(",")] if info_columns else VideoInfo.INFO_COLUMNS
        )
        if ids_file_path:
            ids += cls.data_from_csv(ids_file_path, id_column_name)
        if urls_file_path:
            urls += cls.data_from_csv(urls_file_path, url_column_name)

        if not ids and not urls:
            raise Exception("Either 'ids', 'urls' must be provided for the video-info command")

        youtube = YouTube([api_key], disable_ipv6=True)

        if urls:
            ids += sum([cls.video_id_from_url(url) for url in urls], [])

        # Remove duplicated
        ids = list(set(ids))
        videos_infos = list(youtube.videos_infos([_id for _id in ids if _id]))
        return cls.data_to_csv(
            data=[VideoInfo.filter_fields(video_info, info_columns) for video_info in videos_infos],
            output_file_path=output_file_path,
        )
