from chat_downloader.sites.youtube import YouTubeChatDownloader
from chat_downloader.utils.core import float_or_none, multi_get, parse_iso8601, regex_search, try_parse_json


class YouTubeCD(YouTubeChatDownloader):
    """
    YouTube Chat Downloader subclass to fix YouTube data parsing issues
    """

    def _parse_video_data(self, video_id, params=None, video_type="video"):
        details = {}

        if video_type == "clip":
            original_url = self._YT_CLIP_TEMPLATE.format(video_id)
        else:  # video_type == 'video'
            original_url = self._YT_VIDEO_TEMPLATE.format(video_id)

        yt_initial_data, ytcfg, player_response_info = self._get_initial_info(original_url, params)

        streaming_data = player_response_info.get("streamingData") or {}
        first_format = multi_get(streaming_data, "adaptiveFormats", 0) or multi_get(streaming_data, "formats", 0) or {}

        # Live streaming details
        player_renderer = multi_get(player_response_info, "microformat", "playerMicroformatRenderer") or {}
        live_details = player_renderer.get("liveBroadcastDetails") or {}

        # Video info
        video_details = player_response_info.get("videoDetails") or {}
        details["title"] = video_details.get("title")
        details["author"] = video_details.get("author")
        details["author_id"] = video_details.get("channelId")
        details["original_video_id"] = video_details.get("videoId")

        # Clip info
        clip_details = player_response_info.get("clipConfig")
        if clip_details:
            details["clip_start_time"] = float_or_none(clip_details.get("startTimeMs", 0)) / 1e3
            details["clip_end_time"] = float_or_none(clip_details.get("endTimeMs", 0)) / 1e3
            details["video_type"] = "clip"

        elif not video_details.get("isLiveContent"):
            details["video_type"] = "premiere"

        else:
            details["video_type"] = "video"

        start_timestamp = live_details.get("startTimestamp")
        end_timestamp = live_details.get("endTimestamp")
        details["start_time"] = parse_iso8601(start_timestamp) if start_timestamp else None
        details["end_time"] = parse_iso8601(end_timestamp) if end_timestamp else None

        details["duration"] = (
            (float_or_none(first_format.get("approxDurationMs", 0)) / 1e3)
            or float_or_none(video_details.get("lengthSeconds"))
            or float_or_none(player_renderer.get("lengthSeconds"))
        )

        if not details["duration"] and details["start_time"] and details["end_time"]:
            details["duration"] = (details["end_time"] - details["start_time"]) / 1e6

        # Parse continuation info
        sub_menu_items = (
            multi_get(
                yt_initial_data,
                "contents",
                "twoColumnWatchNextResults",
                "conversationBar",
                "liveChatRenderer",
                "header",
                "liveChatHeaderRenderer",
                "viewSelector",
                "sortFilterSubMenuRenderer",
                "subMenuItems",
            )
            or {}
        )
        details["continuation_info"] = {
            x["title"]: x["continuation"]["reloadContinuationData"]["continuation"] for x in sub_menu_items
        }

        # live, upcoming or past
        if video_details.get("isLive") or live_details.get("isLiveNow"):
            details["status"] = "live"

        elif video_details.get("isUpcoming"):
            details["status"] = "upcoming"

        else:
            details["status"] = "past"

        try:
            client_continuation = yt_initial_data["contents"]["twoColumnWatchNextResults"]["conversationBar"][
                "liveChatRenderer"
            ]["continuations"][0]["reloadContinuationData"]["continuation"]

            if details["status"] != "past":
                response = self._session_get(f"https://www.youtube.com/live_chat?continuation={client_continuation}")
            else:
                response = self._session_get(
                    f"https://www.youtube.com/live_chat_replay?continuation={client_continuation}"
                )

            html = response.text
            yt = regex_search(html, self._YT_INITIAL_DATA_RE)
            dictLiveChats = try_parse_json(yt)

            continuations = dictLiveChats["continuationContents"]["liveChatContinuation"]["header"][
                "liveChatHeaderRenderer"
            ]["viewSelector"]["sortFilterSubMenuRenderer"]["subMenuItems"]

            top_continuation = continuations[0]["continuation"]["reloadContinuationData"]["continuation"]
            live_continuation = continuations[1]["continuation"]["reloadContinuationData"]["continuation"]

            if details["status"] != "past":
                details["continuation_info"]["Top chat"] = top_continuation
                details["continuation_info"]["Live chat"] = live_continuation
            else:
                details["continuation_info"]["Top chat replay"] = top_continuation
                details["continuation_info"]["Live chat replay"] = live_continuation
        except:
            pass

        return details, player_response_info, yt_initial_data, ytcfg
