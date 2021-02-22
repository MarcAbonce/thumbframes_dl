import math
from typing import Dict, List

from youtube_dl.utils import try_get, int_or_none
from youtube_dl.extractor.youtube import YoutubeIE

from ._base import WebsiteFrames, ThumbFramesImage
from thumbframes_dl.utils import logger


class YouTubeFrames(WebsiteFrames, YoutubeIE):
    _YOUTUBE_URL = 'https://www.youtube.com'
    _VIDEO_WEBPAGE_URL = _YOUTUBE_URL + '/watch?v={VIDEO_ID}'
    _VIDEO_INFO_URL = _YOUTUBE_URL + '/get_video_info?video_id={VIDEO_ID}&el=detailpage'

    def _validate(self):
        self._video_id = YoutubeIE.extract_id(self._input_url)

    @property
    def video_id(self):
        return self._video_id

    @property
    def video_url(self):
        return self._VIDEO_WEBPAGE_URL.format(VIDEO_ID=self.video_id)

    # Try to extract storyboard spec from player_response object
    def _get_storyboard_spec(self):
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

    # Extract information of each storyboard
    def _get_storyboards_from_spec(self, video_id, sb_spec):
        storyboards = dict()

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

            storyboards_url = base_url.replace('$L', str(i)) + '&'
            storyboard_set = []
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

    def download_thumbframe_info(self) -> Dict[str, List[ThumbFramesImage]]:
        sb_spec = self._get_storyboard_spec()
        if not sb_spec:
            logger.warning('Could not find thumbframes for video {}'.format(self.video_id))
            return dict()

        return self._get_storyboards_from_spec(self.video_id, sb_spec)
