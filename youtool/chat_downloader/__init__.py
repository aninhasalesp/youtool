import itertools
import time
from urllib.parse import urlparse

from chat_downloader.chat_downloader import ChatDownloader
from chat_downloader.debugging import log
from chat_downloader.errors import ChatGeneratorError, InvalidURL, SiteNotSupported, URLNotProvided
from chat_downloader.formatting.format import ItemFormatter
from chat_downloader.output.continuous_write import ContinuousWriter
from chat_downloader.sites.common import SiteDefault
from chat_downloader.utils.timed_utils import TimedGenerator

from .youtube import YouTubeCD


class YouToolChatDownloader(ChatDownloader):
    """
    YouTool Chat Downloader subclass to fix YouTube data parsing issues
    """

    def get_chat(
        self,
        url=None,
        start_time=None,
        end_time=None,
        max_attempts=15,
        retry_timeout=None,
        interruptible_retry=True,
        timeout=None,
        inactivity_timeout=None,
        max_messages=None,
        message_groups=SiteDefault("message_groups"),
        message_types=None,
        output=None,
        overwrite=True,
        sort_keys=True,
        indent=4,
        format=SiteDefault("format"),
        format_file=None,
        chat_type="live",
        ignore=None,
        message_receive_timeout=0.1,
        buffer_size=4096,
    ):
        """
        Override get_chat to use YouTubeCD instead of YouTubeChatDownloader
        """
        if not url:
            raise URLNotProvided("No URL provided.")

        original_params = locals()
        original_params.pop("self")

        # loop through all websites and
        # get corresponding website parser
        # based on matching url with predefined regex
        site = YouTubeCD
        match_info = site.matches(url)
        if match_info:  # match found

            function_name, match = match_info

            # Create new session
            self.create_session(site)
            site_object = self.sessions[site.__name__]

            # Parse site-defaults
            params = {}
            for k, v in original_params.items():
                params[k] = site_object.get_site_value(v)

            log("info", f"Site: {site_object._NAME}")
            log("debug", f"Program parameters: {params}")

            get_chat = getattr(site_object, function_name, None)
            if not get_chat:
                raise NotImplementedError(f"{function_name} has not been implemented in {site.__name__}.")

            chat = get_chat(match, params)
            log("debug", f'Match found: "{match}". Running "{function_name}" function in "{site.__name__}".')

            if chat is None:
                raise ChatGeneratorError(f'No valid generator found in {site.__name__} for url "{url}"')

            if isinstance(params["max_messages"], int):
                chat.chat = itertools.islice(chat.chat, params["max_messages"])
            else:
                pass  # TODO throw error

            if params["timeout"] is not None or params["inactivity_timeout"] is not None:
                # Generator requires timing functionality

                chat.chat = TimedGenerator(chat.chat, params["timeout"], params["inactivity_timeout"])

                if isinstance(params["timeout"], (float, int)):
                    start = time.time()

                    def log_on_timeout():
                        log("debug", f"Timeout occurred after {time.time() - start} seconds.")

                    setattr(chat.chat, "on_timeout", log_on_timeout)

                if isinstance(params["inactivity_timeout"], (float, int)):

                    def log_on_inactivity_timeout():
                        log("debug", f"Inactivity timeout occurred after {params['inactivity_timeout']} seconds.")

                    setattr(chat.chat, "on_inactivity_timeout", log_on_inactivity_timeout)

            formatter = ItemFormatter(params["format_file"])
            chat.format = lambda x: formatter.format(x, format_name=params["format"])

            if params["output"]:
                chat.attach_writer(
                    ContinuousWriter(
                        params["output"],
                        indent=params["indent"],
                        sort_keys=params["sort_keys"],
                        overwrite=params["overwrite"],
                        lazy_initialise=True,
                    )
                )

            chat.site = site_object

            log("debug", f"Chat information: {chat.__dict__}")
            log("info", f'Retrieving chat for "{chat.title}".')

            return chat

        parsed = urlparse(url)
        log("debug", str(parsed))

        if parsed.netloc:
            raise SiteNotSupported(f"Site not supported: {parsed.netloc}")
        elif not parsed.scheme:  # No scheme, try to correct
            original_params["url"] = "https://" + url
            chat = self.get_chat(**original_params)
            if chat:
                return chat
        else:
            raise InvalidURL(f'Invalid URL: "{url}"')
