import math

from typing import Optional

from youtube_dl.utils import try_get, int_or_none
from youtube_dl.extractor.youtube import YoutubeIE

from thumbframes_dl.utils import logger

from .base import WebsiteFrames, ThumbFramesImage


class YouTubeFrames(WebsiteFrames, YoutubeIE):
    """
    Extracts thumbframes (a.k.a. storyboards) from a YouTube video.

    YouTube can return thumbframes images in different formats, such as:

    * L0: A single small image with a 10x10 grid.
    * L1: A set of bigger images with a 10x10 grid each.
    * L2: A set of bigger images with a 5x5 grid each.

    The image sizes may vary per video.
    Also, a video doesn't necessarily contain images in all the formats.
    """

    _YOUTUBE_URL = 'https://www.youtube.com'
    _VIDEO_WEBPAGE_URL = _YOUTUBE_URL + '/watch?v={VIDEO_ID}'
    _VIDEO_INFO_URL = _YOUTUBE_URL + '/get_video_info?video_id={VIDEO_ID}&el=detailpage'

    def _validate(self) -> None:
        """:raises ExtractorError"""
        self._video_id = YoutubeIE.extract_id(self._input_url)

    @property
    def video_id(self) -> str:
        return self._video_id

    @property
    def video_url(self) -> str:
        return self._VIDEO_WEBPAGE_URL.format(VIDEO_ID=self.video_id)

    def _get_storyboard_spec(self) -> Optional[str]:
        """
        Tries to extract storyboard spec from player_response object.
        Storyboard spec is downloaded from video's page or an API endpoint.
        """

        video_id = self.video_id
        webpage_url = self._VIDEO_WEBPAGE_URL.format(VIDEO_ID=video_id)

        webpage = self._download_webpage(
            webpage_url + '&bpctr=9999999999', video_id, fatal=False)

        player_response = None
        if webpage:
            player_response = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_PLAYER_RESPONSE_RE,
                video_id, 'initial player response')
        if not player_response:
            player_response = self._call_api(
                'player', {'videoId': video_id}, video_id)

        if player_response and 'storyboards' in player_response:
            return try_get(player_response,
                           lambda x: x['storyboards']['playerStoryboardSpecRenderer']['spec'],
                           str)

        return None  # storyboard spec not found anywhere in page

    def _get_storyboards_from_spec(self, sb_spec: str) -> dict[str, list[ThumbFramesImage]]:
        """
        Tries to extract information for each storyboard
        by parsing the extracted storyboard spec.
        """

        storyboards: dict[str, list[ThumbFramesImage]] = {}

        s_parts = sb_spec.split('|')
        base_url = s_parts[0]
        for i, params in enumerate(s_parts[1:]):
            storyboard_attrib = params.split('#')
            if len(storyboard_attrib) != 8:
                logger.warning('Unable to extract thumbframe from spec {}'.format(params))
                continue

            frame_width = int_or_none(storyboard_attrib[0])
            frame_height = int_or_none(storyboard_attrib[1])
            total_frames = int_or_none(storyboard_attrib[2])
            cols = int_or_none(storyboard_attrib[3])
            rows = int_or_none(storyboard_attrib[4])
            filename = storyboard_attrib[6]
            sigh = storyboard_attrib[7]

            if frame_width and frame_height and cols and rows and total_frames:
                frames = cols * rows
                width, height = frame_width * cols, frame_height * rows
                n_images = int(math.ceil(total_frames / float(cols * rows)))
            else:
                logger.warning('Unable to extract thumbframe from spec {}'.format(params))
                continue

            storyboard_set: list[ThumbFramesImage] = []
            storyboards_url = base_url.replace('$L', str(i)) + '&'
            for j in range(n_images):
                url = storyboards_url.replace('$N', filename).replace('$M', str(j)) + 'sigh=' + sigh
                if j == n_images - 1:
                    remaining_frames = total_frames % (cols * rows)
                    if remaining_frames != 0:
                        frames = remaining_frames
                        rows = int(math.ceil(float(remaining_frames) / rows))
                        height = rows * frame_height
                        if rows == 1:
                            cols = remaining_frames
                            width = cols * frame_width

                storyboard_set.append(
                    ThumbFramesImage(
                        url=url,
                        width=width,
                        height=height,
                        cols=cols,
                        rows=rows,
                        n_frames=frames)
                )
            storyboards['L{}'.format(i)] = storyboard_set

        return storyboards

    def download_thumbframe_info(self) -> dict[str, list[ThumbFramesImage]]:
        sb_spec = self._get_storyboard_spec()
        if not sb_spec:
            logger.warning('Could not find thumbframes for video {}'.format(self.video_id))
            return dict()

        return self._get_storyboards_from_spec(sb_spec)
