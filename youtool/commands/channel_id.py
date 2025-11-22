from pathlib import Path

from youtool import YouTube

from .base import Command


class ChannelId(Command):
    """Get channel IDs from a list of URLs (or CSV filename with URLs inside), generate CSV output (just the IDs)."""

    name = "channel-id"
    arguments = [
        {
            "name": "--urls",
            "short": "-u",
            "type": str,
            "help": "Channels urls",
            "nargs": "*",
            "mutually_exclusive_group": "input_source",
        },
        {
            "name": "--urls-file-path",
            "short": "-f",
            "type": Path,
            "help": "Channels urls csv file path",
            "mutually_exclusive_group": "input_source",
        },
        {"name": "--output-file-path", "short": "-o", "type": Path, "help": "Output csv file path"},
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
                urls (list[str]): List of YouTube channel URLs.
                    Mutually exclusive with `urls_file_path`.
                urls_file_path (Path): Path to a CSV file containing YouTube channel URLs.
                    Mutually exclusive with `urls`.
                    Requires url_column_name to specify the column with URLs.
                output_file_path (Path, optional): Path to the output CSV file where channel IDs will be saved.
                    If not provided, the result will be returned as a string.
                api_key (str): The API key to authenticate with the YouTube Data API.
                url_column_name (str, optional): The name of the column in the urls_file_path CSV file that contains the URLs.
                    Default is "url".
                id_column_name (str, optional): The name of the column for channel IDs in the output CSV file.
                    Default is "channel_id".

        Returns:
            str: A message indicating the result of the command. If output_file_path is specified, the message will
                 include the path to the generated CSV file. Otherwise, it will return the result as a string.

        Raises:
            ValueError: If neither `urls` nor `urls_file_path` is provided, or if both are provided at the same time.
        """
        urls = kwargs.get("urls") or []
        urls_file_path = kwargs.get("urls_file_path")
        output_file_path = kwargs.get("output_file_path")
        api_key = kwargs.get("api_key")

        url_column_name = kwargs.get("url_column_name")
        id_column_name = kwargs.get("id_column_name")

        urls = cls.resolve_urls(urls, urls_file_path, url_column_name)

        youtube = YouTube([api_key], disable_ipv6=True)

        channels_ids = [youtube.channel_id_from_url(url) for url in urls if url]

        result = cls.data_to_csv(
            data=[{(id_column_name or cls.CHANNEL_ID_COLUMN_NAME): channel_id} for channel_id in channels_ids],
            output_file_path=output_file_path,
        )

        return result

    @classmethod
    def resolve_urls(cls, urls, urls_file_path, url_column_name):
        if urls_file_path:
            urls += cls.data_from_csv(
                file_path=Path(urls_file_path), data_column_name=url_column_name or cls.URL_COLUMN_NAME
            )
        if not urls:
            raise Exception("Either 'username' or 'url' must be provided for the channel-id command")
        return urls
