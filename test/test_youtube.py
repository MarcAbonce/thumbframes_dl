from numbers import Number
from unittest import mock, TestCase
from urllib.parse import urlparse

from thumbframes_dl import YouTubeFrames, ExtractorError

from . import get_video_html


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
        video = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertIsNone(video._thumbframes)

    def test_page_only_downloads_once(self, mock_download_page):
        # construct object lazily so nothing is downloaded yet
        video = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertFalse(mock_download_page.called)

        # call thumbframes property, which should now call download
        video.thumbframes
        self.assertTrue(mock_download_page.called)
        self.assertEqual(mock_download_page.call_count, 1)

        # should NOT download again if thumbframes property has already been calculated before
        video.thumbframes
        self.assertEqual(mock_download_page.call_count, 1)

    def test_get_thumbframes(self, mock_download_page):
        required_numbers = ['width', 'height', 'cols', 'rows', 'frames']

        video = YouTubeFrames(self.VIDEO_ID)
        self.assertIsNotNone(video.thumbframes)

        for i in range(3):
            tf_id = 'L{}'.format(i)
            self.assertIn(tf_id, video.thumbframes)
            for tf in video.thumbframes[tf_id]:
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

    #def test_thumbframes_not_found(self, mock_download_page):
    #    DUMMY_VIDEO_ID = 'XXXXXXXXXXX'
    #    video = YouTubeFrames(DUMMY_VIDEO_ID)
    #    self.assertIsNotNone(video.thumbframes)
