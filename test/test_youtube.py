import unittest

from thumbframes_dl.ytdl_utils.utils import ExtractorError
from thumbframes_dl import YouTubeFrames


class TestYouTubeFrames(unittest.TestCase):
    VIDEO_ID = 'WhWc3b3KhnY'
    VIDEO_URL = 'https://www.youtube.com/watch?v=WhWc3b3KhnY'

    def test_get_url_from_id(self):
        video_frames = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertEqual(video_frames._extract_id(self.VIDEO_ID), self.VIDEO_ID)

    def test_parse_url(self):
        video_frames = YouTubeFrames(self.VIDEO_URL, lazy=True)
        self.assertEqual(video_frames._extract_id(self.VIDEO_URL), self.VIDEO_ID)

    def test_fail_with_bad_url(self):
        BAD_URL = 'BAD_URL'
        video_frames = YouTubeFrames(BAD_URL, lazy=True)
        with self.assertRaises(ExtractorError):
            video_frames._extract_id(BAD_URL)

    def test_lazy_parameter(self):
        video_frames = YouTubeFrames(self.VIDEO_ID, lazy=True)
        self.assertIsNone(video_frames._thumbframes)
