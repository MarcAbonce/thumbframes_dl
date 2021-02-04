import re
from numbers import Number
from unittest import mock, TestCase
from urllib.parse import urlparse

from thumbframes_dl import YouTubeFrames, ExtractorError

from . import get_video_html, get_empty_html, get_empty_image


@mock.patch('thumbframes_dl.extractors._base.ThumbFramesImage._download_image', side_effect=get_empty_image)
@mock.patch('thumbframes_dl.YouTubeFrames._download_page', side_effect=get_video_html)
class TestYouTubeFrames(TestCase):

    # Spring | Blender Animation Studio | CC BY 4.0
    VIDEO_ID = 'WhWc3b3KhnY'
    VIDEO_URL = 'https://www.youtube.com/watch?v=WhWc3b3KhnY'

    # Assert that ThumbFramesImage objects look reasonably well
    def assertThumbFrames(self, tf_images):
        self.assertIsNotNone(tf_images)
        self.assertTrue(tf_images)

        for tf_image in tf_images:
            # check that all required numbers are set
            self.assertIsInstance(tf_image.width, Number)
            self.assertIsInstance(tf_image.height, Number)
            self.assertIsInstance(tf_image.cols, Number)
            self.assertIsInstance(tf_image.rows, Number)
            self.assertIsInstance(tf_image.n_frames, Number)

            # check that url makes sense
            tf_url = urlparse(tf_image.url)
            self.assertIn('http', tf_url.scheme)
            self.assertIn('ytimg.com', tf_url.netloc)
            self.assertIn('storyboard', tf_url.path)
            self.assertIn('.jpg', tf_url.path)
            self.assertNotEqual(tf_url.query, '')

            # check that image is set
            self.assertIsNotNone(tf_image.image)

    def test_init_with_video_id(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_ID)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_init_with_video_url(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_URL)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_fail_init_with_bad_url(self, mock_download_page, mock_download_image):
        BAD_URL = 'BAD_URL'
        with self.assertRaises(ExtractorError):
            _ = YouTubeFrames(BAD_URL)

    def test_thumbframes_not_found(self, mock_download_page, mock_download_image):
        mock_download_page.side_effect = get_empty_html

        video = YouTubeFrames('DUMMY_VIDEO')

        # downloaded both webpage and video_info to try to find thumbframes
        self.assertEqual(mock_download_page.call_count, 2)

        # thumbframes info is an empty structure but NOT a None
        self.assertIsNotNone(video._thumbframes)
        self.assertFalse(video._thumbframes)

        # should NOT re-try download even if thumbframes info is empty
        self.assertEqual(mock_download_page.call_count, 2)

    def test_page_only_downloads_once(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads page with frames info
        self.assertIsNotNone(video.get_thumbframes('L0'))
        self.assertTrue(mock_download_page.called)
        self.assertEqual(mock_download_page.call_count, 1)

        mock_download_page.reset_mock()

        # should NOT download again if thumbframes data has already been obtained before
        self.assertIsNotNone(video.get_thumbframes('L1'))
        self.assertFalse(mock_download_page.called)
        self.assertEqual(mock_download_page.call_count, 0)

    def test_images_only_download_once(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads each image
        thumbframes = video.get_thumbframes('L2')
        for tf_image in video.get_thumbframes('L2'):
            self.assertIsNotNone(tf_image.image)
        self.assertTrue(mock_download_image.called)
        self.assertEqual(mock_download_image.call_count, len(thumbframes))

        mock_download_image.reset_mock()

        # should NOT download images again if they have already been downloaded before
        same_thumbframes_as_before = video.get_thumbframes('L2')
        for tf_image in same_thumbframes_as_before:
            self.assertIsNotNone(tf_image.image)
        self.assertFalse(mock_download_image.called)
        self.assertEqual(mock_download_image.call_count, 0)

    def test_lazy_thumbframes(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads each image
        for counter, tf_image in enumerate(video.get_thumbframes('L2'), start=1):
            self.assertIsNotNone(tf_image.image)
            self.assertTrue(mock_download_image.called)
            self.assertEqual(mock_download_image.call_count, counter)

    def test_non_lazy_thumbframes(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_ID)

        # call method in non lazy mode so all images are downloaded right away
        thumbframes = video.get_thumbframes('L2', lazy=False)
        self.assertTrue(mock_download_image.called)
        self.assertEqual(mock_download_image.call_count, len(thumbframes))

        mock_download_image.reset_mock()

        # no additional download here because images are already set
        for tf_image in thumbframes:
            self.assertIsNotNone(tf_image.image)
            self.assertFalse(mock_download_image.called)
        self.assertEqual(mock_download_image.call_count, 0)

    # Test that internal _thumbframes dict is set correctly.
    def test_get_thumbframes_info(self, mock_download_page, mock_download_image):

        video = YouTubeFrames(self.VIDEO_ID)

        self.assertIsNotNone(video._thumbframes)
        self.assertTrue(video._thumbframes)
        self.assertEqual(len(video._thumbframes), 3)

        for i in range(3):
            tf_id = 'L{}'.format(i)
            self.assertIn(tf_id, video._thumbframes)
            self.assertThumbFrames(video._thumbframes[tf_id])

    def test_get_thumbframes(self, mock_download_page, mock_download_image):
        video = YouTubeFrames(self.VIDEO_ID)

        # download 1 image from the L0 set
        self.assertThumbFrames(video.get_thumbframes('L0'))
        self.assertEqual(mock_download_page.call_count, 1)
        self.assertEqual(mock_download_image.call_count, 1)

        # download 1 image from the L1 set
        mock_download_page.reset_mock()
        mock_download_image.reset_mock()
        self.assertThumbFrames(video.get_thumbframes('L1'))
        self.assertEqual(mock_download_page.call_count, 0)
        self.assertEqual(mock_download_image.call_count, 1)

        # download 4 images from the L2 set
        mock_download_page.reset_mock()
        mock_download_image.reset_mock()
        self.assertThumbFrames(video.get_thumbframes('L2'))
        self.assertEqual(mock_download_page.call_count, 0)
        self.assertEqual(mock_download_image.call_count, 4)

    def test_get_thumbframes_from_webpages_initial_player_response(self, mock_download_page, mock_download_image):
        # return webpage without ytplayer.config object so it looks up the ytInitialPlayerResponse object instead
        original_side_effect = mock_download_page.side_effect
        def _get_webpage_without_ytplayer_config(url, *args, **kwargs):  # noqa: E306
            webpage = original_side_effect(url, *args, **kwargs)
            return re.sub(r'\<script\>.*ytplayer\.config.*\<\/script\>', '', webpage)
        mock_download_page.side_effect = _get_webpage_without_ytplayer_config

        # check thumbframes
        video = YouTubeFrames(self.VIDEO_ID)
        self.assertThumbFrames(video.get_thumbframes('L0'))

        # result is still found in webpage, therefore no need to download video_info
        self.assertEqual(mock_download_page.call_count, 1)

    def test_get_thumbframes_from_video_info(self, mock_download_page, mock_download_image):
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
        self.assertThumbFrames(video.get_thumbframes('L0'))

        # downloaded both webpage and video_info to try to find thumbframes
        self.assertEqual(mock_download_page.call_count, 2)
