from numbers import Number
from unittest import mock, TestCase
from urllib.parse import urlparse

from thumbframes_dl import YouTubeFrames, ExtractorError


class TestYouTubeFrames(TestCase):
    # Spring | Blender Animation Studio | CC BY 4.0
    VIDEO_ID = 'WhWc3b3KhnY'
    VIDEO_URL = 'https://www.youtube.com/watch?v=WhWc3b3KhnY'
    VIDEO_HTML_PATH = './test_assets/2020_11_28_WhWc3b3KhnY.html'

    #def _get_video_html(self, *args, **kwargs):
    #    with open(VIDEO_HTML_PATH) as f:
    #        return f.read()

    def test_init_with_video_id(self):
        video = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_init_with_video_url(self):
        video = YouTubeFrames(self.VIDEO_URL, lazy=True)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_fail_init_with_bad_url(self):
        BAD_URL = 'BAD_URL'
        with self.assertRaises(ExtractorError):
            video = YouTubeFrames(BAD_URL, lazy=True)

    def test_lazy_parameter(self):
        video = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertIsNone(video._thumbframes)

    #@mock.patch('thumbframes_dl.YouTubeFrames._download_page', _get_video_html)
    #def test_only_downloads_once(self):
    #    video = YouTubeFrames(self.VIDEO_ID, lazy=True)

    #@mock.patch('thumbframes_dl.YouTubeFrames._download_page', _get_video_html)
    def test_get_thumbframes(self):
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
