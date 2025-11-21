from pathlib import Path

from youtool import YouTube

from .base import Command


class VideoTranscription(Command):
    """Download video transcriptions from YouTube videos based on IDs or URLs (or CSV filename with URLs/IDs inside), and save them to files."""

    name = "video-transcription"
    arguments = [
        {"name": "--ids", "type": str, "help": "Video IDs", "nargs": "*", "mutually_exclusive_group": "input_source"},
        {"name": "--urls", "type": str, "help": "Video URLs", "nargs": "*", "mutually_exclusive_group": "input_source"},
        {
            "name": "--urls-file-path",
            "type": Path,
            "help": "Channels urls csv file path",
            "mutually_exclusive_group": "input_source",
        },
        {"name": "--ids-file-path", "type": Path, "help": "Channel IDs CSV file path", "mutually_exclusive_group": "input_source"},
        {"name": "--output-dir", "type": Path, "help": "Output directory to save transcriptions", "required": True},
        {"name": "--language-code", "type": str, "help": "Language code for transcription", "required": True},
        {"name": "--url_column_name", "type": str, "help": "URL column name on CSV input files"},
        {"name": "--id_column_name", "type": str, "help": "ID column name on CSV input files"},
    ]

    ID_COLUMN_NAME: str = "video_id"
    URL_COLUMN_NAME: str = "video_url"

    @classmethod
    def execute(cls, **kwargs) -> str:
        """Execute the video-transcription command to download transcriptions of videos from IDs or URLs and save them to a CSV file.

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
            output_dir (Path, optional): Path to the output CSV file where video information will be saved.
            language_code (str): Language code for the transcription language.
            api_key (str): The API key to authenticate with the YouTube Data API.
            url_column_name (str, optional): Column name for URLs in the CSV input file. Defaults to "video_url".
            id_column_name (str, optional): Column name for IDs in the CSV output file. Defaults to "video_id".

        Returns:
            str: A message indicating the result of the command. Reports success or failure for each video transcription download.
        """
        ids = kwargs.get("ids") or []
        urls = kwargs.get("urls") or []
        ids_file_path = kwargs.get("ids_file_path")
        urls_file_path = kwargs.get("urls_file_path")
        output_dir = kwargs.get("output_dir")
        language_code = kwargs.get("language_code")
        api_key = kwargs.get("api_key")

        url_column_name = kwargs.get("url_column_name") or VideoTranscription.URL_COLUMN_NAME
        id_column_name = kwargs.get("id_column_name") or VideoTranscription.ID_COLUMN_NAME

        youtube = YouTube([api_key], disable_ipv6=True)

        if ids_file_path:
            ids += cls.data_from_csv(ids_file_path, id_column_name)
        if urls_file_path:
            urls += cls.data_from_csv(urls_file_path, url_column_name)

        if not ids and not urls:
            raise Exception("Either 'ids' or 'urls' must be provided for the video-transcription command")

        if urls:
            ids += sum([cls.video_id_from_url(url) for url in urls], [])

        # Remove duplicated
        ids = list(set(ids))
        youtube.videos_transcriptions(ids, language_code, output_dir)
        output_dir_path = Path(output_dir)
        saved_transcriptions = [
            str(output_dir_path / f"{v_id}.{language_code}.vtt")
            for v_id in ids
            if (output_dir_path / f"{v_id}.{language_code}.vtt").is_file()
        ]
        return "\n".join(saved_transcriptions)
