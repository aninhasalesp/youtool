from pathlib import Path
from typing import List, Self

from youtool import YouTube

from .base import Command


class ChannelInfo(Command):
    """Get channel info from a list of IDs (or CSV filename with IDs inside), generate CSV output
    (same schema for `channel` dicts)
    """

    name = "channel-info"
    arguments = [
        {
            "name": "channel_references",
            "type": str,
            "nargs": "+",
            "help": "Channel URLs, usernames (@), IDs or CSV file paths",
        },
        {"name": "--output", "short": "-o", "type": Path, "help": "Output CSV file path"},
        {"name": "--url-column-name", "short": "-c", "type": str, "help": "URL column name on CSV input files"},
        {
            "name": "--username-column-name",
            "short": "-s",
            "type": str,
            "help": "Username column name on CSV input files",
        },
        {"name": "--id-column-name", "short": "-a", "type": str, "help": "ID column name on CSV input files"},
    ]

    URL_COLUMN_NAME: str = "channel_url"
    USERNAME_COLUMN_NAME: str = "channel_username"
    ID_COLUMN_NAME: str = "channel_id"
    INFO_COLUMNS: List[str] = [
        "id",
        "title",
        "description",
        "published_at",
        "view_count",
        "subscriber_count",
        "video_count",
    ]

    @classmethod
    def execute(cls: Self, **kwargs) -> str:
        """Execute the channel-info command to fetch YouTube channel information from various references and save them to a CSV file.

        Args:
            channel_references (list[str]): List of YouTube channel URLs, usernames, IDs, or CSV file paths.
            output (Path, optional): Path to the output CSV file where channel information will be saved.
            api_key (str): The API key to authenticate with the YouTube Data API.
            url_column_name (str, optional): The name of the column in the `urls_file_path` CSV file that contains the URLs.
                                            Default is "channel_url".
            username_column_name (str, optional): The name of the column in the `usernames_file_path` CSV file that contains the usernames.
                                            Default is "channel_username".
            info_columns (str, optional): Comma-separated list of columns to include in the output CSV.
                                            Default is the class attribute `INFO_COLUMNS`.

        Returns:
            str: A message indicating the result of the command. If `output` is specified, the message will
                include the path to the generated CSV file. Otherwise, it will return the result as a string.

        Raises:
            Exception: If no valid channel references are provided.
        """

        references = kwargs["channel_references"]
        output = kwargs.get("output")
        api_key = kwargs.get("api_key")

        url_column_name = kwargs.get("url_column_name") or ChannelInfo.URL_COLUMN_NAME
        username_column_name = kwargs.get("username_column_name") or ChannelInfo.USERNAME_COLUMN_NAME
        id_column_name = kwargs.get("id_column_name") or ChannelInfo.ID_COLUMN_NAME
        info_columns = kwargs.get("info_columns")

        info_columns = (
            [column.strip() for column in info_columns.split(",")] if info_columns else ChannelInfo.INFO_COLUMNS
        )

        parsed = cls.parse_references(references)

        youtube = YouTube([api_key], disable_ipv6=True)

        urls = parsed["urls"]

        urls.extend(url for path in parsed["file_paths"] for url in cls.data_from_csv(path, url_column_name))

        usernames_from_files = (
            username for path in parsed["file_paths"] for username in cls.data_from_csv(path, username_column_name)
        )

        usernames = parsed["usernames"] + list(usernames_from_files)

        ids_from_files = (
            channel_id for path in parsed["file_paths"] for channel_id in cls.data_from_csv(path, id_column_name)
        )

        ids = parsed["video_ids"] + list(ids_from_files)

        channel_ids = set(
            [youtube.channel_id_from_url(url) for url in urls if url]
            + [youtube.channel_id_from_username(username) for username in usernames if username]
            + [channel_id for channel_id in ids if channel_id]
        )

        channel_infos = youtube.channels_infos(list(channel_ids)) or []

        return cls.data_to_csv(
            data=[cls.filter_fields(info, info_columns) for info in channel_infos if info],
            output=output,
        )
