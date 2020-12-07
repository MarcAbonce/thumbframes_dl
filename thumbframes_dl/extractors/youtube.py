import math
import re
import urllib

from ._base import FramesExtractor
from thumbframes_dl import logger
from thumbframes_dl.ytdl_utils.utils import try_get, uppercase_escape, int_or_none, str_or_none, ExtractorError


class YouTubeFrames(FramesExtractor):
    _YOUTUBE_URL = 'https://www.youtube.com'
    _VIDEO_WEBPAGE_URL = _YOUTUBE_URL + '/watch?v={VIDEO_ID}'
    _VIDEO_INFO_URL = _YOUTUBE_URL + '/get_video_info?video_id={VIDEO_ID}&el=detailpage'
    _NTH_THUMBNAIL_URL = 'https://i1.ytimg.com/vi/{VIDEO_ID}/{THUMB_NUMBER}.jpg'

    _VALID_URL = r"""(?x)^
                     (
                         (?:https?://|//)                                    # http(s):// or protocol-independent URL
                         (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie|kids)?\.com/|
                            (?:www\.)?deturl\.com/www\.youtube\.com/|
                            (?:www\.)?pwnyoutube\.com/|
                            (?:www\.)?hooktube\.com/|
                            (?:www\.)?yourepeat\.com/|
                            tube\.majestyc\.net/|
                            # Invidious instances taken from https://github.com/omarroth/invidious/wiki/Invidious-Instances
                            (?:(?:www|dev)\.)?invidio\.us/|
                            (?:(?:www|no)\.)?invidiou\.sh/|
                            (?:(?:www|fi|de)\.)?invidious\.snopyta\.org/|
                            (?:www\.)?invidious\.kabi\.tk/|
                            (?:www\.)?invidious\.13ad\.de/|
                            (?:www\.)?invidious\.mastodon\.host/|
                            (?:www\.)?invidious\.nixnet\.xyz/|
                            (?:www\.)?invidious\.drycat\.fr/|
                            (?:www\.)?tube\.poal\.co/|
                            (?:www\.)?vid\.wxzm\.sx/|
                            (?:www\.)?yewtu\.be/|
                            (?:www\.)?yt\.elukerio\.org/|
                            (?:www\.)?yt\.lelux\.fi/|
                            (?:www\.)?invidious\.ggc-project\.de/|
                            (?:www\.)?yt\.maisputain\.ovh/|
                            (?:www\.)?invidious\.13ad\.de/|
                            (?:www\.)?invidious\.toot\.koeln/|
                            (?:www\.)?invidious\.fdn\.fr/|
                            (?:www\.)?watch\.nettohikari\.com/|
                            (?:www\.)?kgg2m7yk5aybusll\.onion/|
                            (?:www\.)?qklhadlycap4cnod\.onion/|
                            (?:www\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\.onion/|
                            (?:www\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\.onion/|
                            (?:www\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\.onion/|
                            (?:www\.)?invidious\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\.onion/|
                            (?:www\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\.b32\.i2p/|
                            (?:www\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\.onion/|
                            youtube\.googleapis\.com/)                        # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/(?!videoseries))                # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?[&;])??                                # any other preceding param (like /?s=tuff&v=xxxx or ?s=tuff&amp;v=V36LpHqtcDY)
                                 v=
                             )
                         ))
                         |(?:
                            youtu\.be|                                        # just youtu.be/xxxx
                            vid\.plus|                                        # or vid.plus/xxxx
                            zwearz\.com/watch|                                # or zwearz.com/watch/xxxx
                         )/
                         |(?:www\.)?cleanvideosearch\.com/media/action/yt/watch\?videoId=
                         )
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]{11})                                      # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""

    def _validate(self):
        self._video_id = self._extract_id(self._input_url)

    @property
    def video_id(self):
        return self._video_id

    @property
    def video_url(self):
        return self._VIDEO_WEBPAGE_URL.format(VIDEO_ID=self.video_id)

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url, expected=True)
        video_id = mobj.group(2)
        return video_id

    def _get_ytplayer_config(self, video_id, webpage):
        patterns = (
            # User data may contain arbitrary character sequences that may affect
            # JSON extraction with regex, e.g. when '};' is contained the second
            # regex won't capture the whole JSON. Yet working around by trying more
            # concrete regex first keeping in mind proper quoted string handling
            # to be implemented in future that will replace this workaround (see
            # https://github.com/ytdl-org/youtube-dl/issues/7468,
            # https://github.com/ytdl-org/youtube-dl/pull/7599)
            r';ytplayer\.config\s*=\s*({.+?});ytplayer',
            r';ytplayer\.config\s*=\s*({.+?});',
        )
        config = self._search_regex(
            patterns, webpage, 'ytplayer.config', default=None)
        if config:
            return self._parse_json(
                uppercase_escape(config), video_id, fatal=False)

    def _extract_player_response(self, player_response, video_id):
        pl_response = str_or_none(player_response)
        if not pl_response:
            return
        pl_response = self._parse_json(pl_response, video_id, fatal=False)
        if isinstance(pl_response, dict):
            return pl_response

    def _extract_sb_spec(self, player_response):
        if player_response and 'storyboards' in player_response:
            return try_get(player_response,
                           lambda x: x['storyboards']['playerStoryboardSpecRenderer']['spec'],
                           str)

    def _get_storyboard_spec(self):
        sb_spec = None

        # Try to extract storyboard spec from video_webpage
        video_webpage = self._download_page(self.video_url)
        player_response = None

        player_config = self._get_ytplayer_config(self.video_id, video_webpage)
        if player_config:
            player_response = self._extract_player_response(
                player_config['args'].get('player_response'),
                self.video_id)

        if not player_response:
            self._YT_INITIAL_PLAYER_RESPONSE_RE = r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;'
            player_response = self._extract_player_response(
                self._search_regex(
                    (r'%s\s*(?:var\s+meta|</script|\n)' % self._YT_INITIAL_PLAYER_RESPONSE_RE,
                     self._YT_INITIAL_PLAYER_RESPONSE_RE), video_webpage,
                    'initial player response', default='{}'),
                self.video_id)

        sb_spec = self._extract_sb_spec(player_response)

        # Try to extract storyboard spec from video_info
        if not sb_spec:
            video_info_page = self._download_page(self._VIDEO_INFO_URL.format(VIDEO_ID=self.video_id))
            video_info = urllib.parse.parse_qs(video_info_page)
            pl_response = video_info.get('player_response', [None])[0]
            player_response = self._extract_player_response(pl_response, self.video_id)
            if player_response:
                sb_spec = self._extract_sb_spec(player_response)
            else:
                sb_spec = video_info.get('storyboard_spec', [None])[0]

        return sb_spec

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

                storyboard_set.append({
                    'id': 'L{0}/M{1}'.format(i, j),
                    'width': width,
                    'height': height,
                    'cols': cols,
                    'rows': rows,
                    'frames': frames,
                    'url': url
                })
            storyboards['L{}'.format(i)] = storyboard_set

        return storyboards

    def _get_thumbframes(self):
        sb_spec = self._get_storyboard_spec()
        if not sb_spec:
            logger.warning('Could not find thumbframes for video {}'.format(self.video_id))
            return dict()

        return self._get_storyboards_from_spec(self.video_id, sb_spec)
