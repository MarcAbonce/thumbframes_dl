import math
import re
import urllib

from . import logger
from .infoextractor import InfoExtractor
from .utils import try_get, uppercase_escape, int_or_none, str_or_none, url_or_none, ExtractorError


class YouTubeIE(InfoExtractor):
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

    def extract_id(self, url):
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

    def extract_player_response(self, player_response, video_id):
        pl_response = str_or_none(player_response)
        if not pl_response:
            return
        pl_response = self._parse_json(pl_response, video_id, fatal=False)
        if isinstance(pl_response, dict):
            return pl_response

    def _extract_sb_spec(self, player_response):
        if 'storyboards' in player_response:
            return try_get(player_response,
                           lambda x: x['storyboards']['playerStoryboardSpecRenderer']['spec'],
                           str)

    # Try to extract storyboard spec from video_info
    def _extract_sb_spec_from_video_info(self, video_id, video_info):
        pl_response = video_info.get('player_response', [None])
        player_response = self.extract_player_response(pl_response, video_id)
        if player_response:
            sb_spec = self._extract_sb_spec(player_response)
        else:
            sb_spec = video_info.get('storyboard_spec')

        return sb_spec

    # Try to extract storyboard spec from video_webpage
    def _extract_sb_spec_from_video_webpage(self, video_id, video_webpage):
        player_config = self._get_ytplayer_config(video_id, video_webpage)
        player_response = self.extract_player_response(
            player_config['args'].get('player_response'),
            video_id)

        sb_spec = self._extract_sb_spec(player_response)
        return sb_spec

    # Extract information of each storyboard
    def _get_storyboards_from_spec(self, video_id, sb_spec):
        storyboards = []

        s_parts = sb_spec.split('|')
        base_url = s_parts[0]
        for i, params in enumerate(s_parts[1:]):
            storyboard_attrib = params.split('#')
            if len(storyboard_attrib) != 8:
                logger.warning('Unable to extract storyboard')
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
                logger.warning('Unable to extract storyboard')
                continue

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

                storyboards.append({
                    'id': 'L' + str(i) + '-M' + str(j),
                    'width': width,
                    'height': height,
                    'cols': cols,
                    'rows': rows,
                    'frames': frames,
                    'url': url
                })

        return storyboards

    def get_storyboards(self, video_url):
        video_id = self.extract_id(video_url)
        video_webpage = self._download_page(self._VIDEO_WEBPAGE_URL.format(VIDEO_ID=video_id))
        sb_spec = self._extract_sb_spec_from_video_webpage(video_id, video_webpage)
        if not sb_spec:
            video_info_page = self._download_page(self._VIDEO_INFO_URL.format(VIDEO_ID=video_id))
            video_info = urllib.parse.parse_qs(video_info_page)
            sb_spec = self._extract_sb_spec_from_video_info(video_id, video_info)
            if not sb_spec:
                logger.warning('Could not find storyboards for video {}'.format(video_id))
                return []

        return self._get_storyboards_from_spec(video_id, sb_spec)

    def get_thumbnails(self, video_id, video_webpage):
        player_config = self._get_ytplayer_config(video_id, video_webpage)
        player_response = self.extract_player_response(
            player_config['args'].get('player_response'),
        video_id)
        video_details = try_get(
            player_response, lambda x: x['videoDetails'], dict) or {}

        thumbnails = []
        thumbnails_list = try_get(
            video_details, lambda x: x['thumbnail']['thumbnails'], list) or []
        for t in thumbnails_list:
            if not isinstance(t, dict):
                continue
            thumbnail_url = url_or_none(t.get('url'))
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(t.get('width')),
                'height': int_or_none(t.get('height')),
            })

        if not thumbnails:
            video_thumbnail = None
            # We try first to get a high quality image:
            m_thumb = re.search(r'<span itemprop="thumbnail".*?href="(.*?)">',
                                video_webpage, re.DOTALL)
            if m_thumb is not None:
                video_thumbnail = m_thumb.group(1)
            # TODO: move
            video_info_page = self._download_page(self._VIDEO_INFO_URL.format(VIDEO_ID=video_id))
            video_info = urllib.parse.parse_qs(video_info_page)
            # --
            thumbnail_url = try_get(video_info, lambda x: x['thumbnail_url'][0], str)
            if thumbnail_url:
                video_thumbnail = urllib.parse.unquote_plus(thumbnail_url)
            if video_thumbnail:
                thumbnails.append({'url': video_thumbnail})

        return thumbnails
