from pathlib import Path
from typing import List

from youtool import YouTube

from .base import Command


class ChannelId(Command):
    """Get channel IDs from a list of URLs (or CSV filename with URLs inside), generate CSV output (just the IDs)."""

    name = "channel-id"
    arguments = [
        {
            "name": "channel_references",
            "type": str,
            "nargs": "+",
            "help": "List of channel URLs or CSV file paths",
        },
        {"name": "--output", "short": "-o", "type": Path, "help": "Output csv file path"},
        {"name": "--url-column-name", "short": "-c", "type": str, "help": "URL column name on csv input files"},
        {"name": "--id-column-name", "short": "-i", "type": str, "help": "Channel ID column name on csv output files"},
    ]

    URL_COLUMN_NAME: str = "channel_url"
    CHANNEL_ID_COLUMN_NAME: str = "channel_id"

    @classmethod
    def execute(cls, **kwargs) -> str:
        """Execute the channel-id command to fetch YouTube channel IDs from URLs and save them to a CSV file.

        This command retrieves YouTube channel IDs from one of two possible inputs:
            - a list of YouTube channel URLs (`--urls`), or
            - a CSV file containing those URLs (`--urls-file-path`).

            Args:
                channel_references (list[str]): List of YouTube channel URLs or CSV file paths.
                output (Path, optional): Path to the output CSV file where channel IDs will be saved.
                    If not provided, the result will be returned as a string.
                api_key (str): The API key to authenticate with the YouTube Data API.
                url_column_name (str, optional): The name of the column in the urls_file_path CSV file that contains the URLs.
                    Default is "url".
                id_column_name (str, optional): The name of the column for channel IDs in the output CSV file.
                    Default is "channel_id".

        Returns:
            str: A message indicating the result of the command. If output is specified, the message will
                 include the path to the generated CSV file. Otherwise, it will return the result as a string.

        Raises:
            ValueError: If neither `urls` nor `urls_file_path` is provided, or if both are provided at the same time.
        """
        channel_references: List[str] = kwargs.get("channel_references", [])
        output = kwargs.get("output")
        api_key = kwargs.get("api_key")

        url_column_name = kwargs.get("url_column_name") or ChannelId.URL_COLUMN_NAME
        id_column_name = kwargs.get("id_column_name") or ChannelId.CHANNEL_ID_COLUMN_NAME

        urls: List[str] = []

        for ref in channel_references:
            if ref.startswith("http"):
                urls.append(ref)
            else:
                # considera que é CSV
                urls += cls.data_from_csv(Path(ref), data_column_name=url_column_name)

        if not urls:
            raise Exception("At least one URL or CSV file path must be provided")

        youtube = YouTube([api_key], disable_ipv6=True)
        channel_ids = [youtube.channel_id_from_url(url) for url in urls if url]

        return cls.data_to_csv(
            data=[{id_column_name: cid} for cid in channel_ids],
            output=output,
        )
