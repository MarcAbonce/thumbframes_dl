import re
from numbers import Number
from unittest import mock, TestCase
from urllib.parse import urlparse

from thumbframes_dl import YouTubeFrames, ExtractorError

from . import get_video_html, get_empty_html


@mock.patch('thumbframes_dl.YouTubeFrames._download_page', side_effect=get_video_html)
class TestYouTubeFrames(TestCase):

    # Spring | Blender Animation Studio | CC BY 4.0
    VIDEO_ID = 'WhWc3b3KhnY'
    VIDEO_URL = 'https://www.youtube.com/watch?v=WhWc3b3KhnY'

    def test_init_with_video_id(self, mock_download_page):
        video = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_init_with_video_url(self, mock_download_page):
        video = YouTubeFrames(self.VIDEO_URL, lazy=True)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_fail_init_with_bad_url(self, mock_download_page):
        BAD_URL = 'BAD_URL'
        with self.assertRaises(ExtractorError):
            _ = YouTubeFrames(BAD_URL, lazy=True)

    def test_lazy_parameter(self, mock_download_page):
        _ = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertFalse(mock_download_page.called)

    def test_page_only_downloads_once(self, mock_download_page):
        # construct object lazily so nothing is downloaded yet
        video = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertFalse(mock_download_page.called)

        # call thumbframes property, which should now call download
        self.assertIsNotNone(video.thumbframes)
        self.assertTrue(mock_download_page.called)
        self.assertEqual(mock_download_page.call_count, 1)

        # should NOT download again if thumbframes property has already been calculated before
        self.assertIsNotNone(video.thumbframes)
        self.assertEqual(mock_download_page.call_count, 1)

    def test_thumbframes_not_found(self, mock_download_page):
        mock_download_page.side_effect = get_empty_html

        video = YouTubeFrames('DUMMY_VIDEO')

        # downloaded both webpage and video_info to try to find thumbframes
        self.assertEqual(mock_download_page.call_count, 2)

        # thumbframes is an empty structure but NOT a None
        self.assertIsNotNone(video.thumbframes)
        self.assertFalse(video.thumbframes)

        # should NOT re-try download even if thumbframes is empty
        self.assertEqual(mock_download_page.call_count, 2)

    # Assert that thumbframes look reasonably well
    def _assert_thumbframes(self, thumbframes, length):
        required_numbers = ['width', 'height', 'cols', 'rows', 'frames']

        self.assertIsNotNone(thumbframes)
        self.assertTrue(thumbframes)

        for i in range(length):
            tf_id = 'L{}'.format(i)
            self.assertIn(tf_id, thumbframes)
            for tf in thumbframes[tf_id]:
                # check that all required numbers are set
                for k in required_numbers:
                    self.assertIn(k, tf)
                    self.assertIsInstance(tf[k], Number)

                # check that url makes sense
                self.assertIn('url', tf)
                tf_url = urlparse(tf['url'])
                self.assertIn('http', tf_url.scheme)
                self.assertIn('ytimg.com', tf_url.netloc)
                self.assertIn('storyboard', tf_url.path)
                self.assertIn('.jpg', tf_url.path)
                self.assertNotEqual(tf_url.query, '')

    def test_get_thumbframes(self, mock_download_page):
        video = YouTubeFrames(self.VIDEO_ID)
        self._assert_thumbframes(video.thumbframes, 3)

    def test_get_thumbframes_from_webpages_initial_player_response(self, mock_download_page):
        # return webpage without ytplayer.config object so it looks up the ytInitialPlayerResponse object instead
        original_side_effect = mock_download_page.side_effect
        def _get_webpage_without_ytplayer_config(url, *args, **kwargs):  # noqa: E306
            webpage = original_side_effect(url, *args, **kwargs)
            return re.sub(r'\<script\>.*ytplayer\.config.*\<\/script\>', '', webpage)
        mock_download_page.side_effect = _get_webpage_without_ytplayer_config

        # check thumbframes
        video = YouTubeFrames(self.VIDEO_ID)
        self._assert_thumbframes(video.thumbframes, 3)

        # result is still found in webpage, therefore no need to download video_info
        self.assertEqual(mock_download_page.call_count, 1)

    def test_get_thumbframes_from_video_info(self, mock_download_page):
        # return webpage without thumbframes so we have to look them up in video_info instead
        original_side_effect = mock_download_page.side_effect
        def _get_empty_webpage(url, *args, **kwargs):  # noqa: E306
            if 'watch' in url:
                return get_empty_html(url)
            else:
                return original_side_effect(url, *args, **kwargs)
        mock_download_page.side_effect = _get_empty_webpage

        # check thumbframes
        video = YouTubeFrames(self.VIDEO_ID)
        self._assert_thumbframes(video.thumbframes, 3)

        # downloaded both webpage and video_info to try to find thumbframes
        self.assertEqual(mock_download_page.call_count, 2)
