from numbers import Number
from unittest import mock, TestCase
from urllib.parse import urlparse

from youtube_dl.utils import ExtractorError
from thumbframes_dl import YouTubeFrames

from . import mock_urlopen, mock_empty_json_response


@mock.patch('youtube_dl.YoutubeDL.urlopen', side_effect=mock_urlopen)
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
            self.assertIsNotNone(tf_image.get_image())

            # check that mime type was set by image, not URL
            self.assertEqual(tf_image.mime_type, 'webp')

    def test_init_with_video_id(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_init_with_video_url(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_URL)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_fail_init_with_bad_url(self, mock_http_request):
        BAD_URL = 'BAD_URL'
        with self.assertRaises(ExtractorError):
            _ = YouTubeFrames(BAD_URL)

    def test_thumbframes_not_found(self, mock_http_request):
        mock_http_request.side_effect = mock_empty_json_response

        # this represents a "valid" YouTube video that returns no thumbframes
        video = YouTubeFrames('ZERO_THUMBS')

        # downloaded both webpage and video_info to try to find thumbframes
        self.assertEqual(mock_http_request.call_count, 2)

        # thumbframes info is an empty structure but NOT a None
        self.assertIsNotNone(video._thumbframes)
        self.assertEqual(len(video.get_thumbframes()), 0)

        # thumbframe formats methods shouldn't break
        self.assertIsNone(video.thumbframe_formats)
        self.assertIsNone(video.get_thumbframe_format())

        # should NOT re-try download even if thumbframes info is empty
        self.assertEqual(mock_http_request.call_count, 2)

    def test_page_only_downloads_once(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads page with frames info
        self.assertIsNotNone(video.get_thumbframes('L0'))
        self.assertTrue(mock_http_request.called)
        self.assertEqual(mock_http_request.call_count, 1)

        mock_http_request.reset_mock()

        # should NOT download again if thumbframes data has already been obtained before
        self.assertIsNotNone(video.get_thumbframes('L1'))
        self.assertFalse(mock_http_request.called)
        self.assertEqual(mock_http_request.call_count, 0)

    def test_images_only_download_once(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)
        mock_http_request.reset_mock()

        # get thumbframes for the first time, which downloads each image
        thumbframes = video.get_thumbframes('L2')
        for tf_image in video.get_thumbframes('L2'):
            self.assertIsNotNone(tf_image.get_image())
        self.assertTrue(mock_http_request.called)
        self.assertEqual(mock_http_request.call_count, len(thumbframes))

        mock_http_request.reset_mock()

        # should NOT download images again if they have already been downloaded before
        same_thumbframes_as_before = video.get_thumbframes('L2')
        for tf_image in same_thumbframes_as_before:
            self.assertIsNotNone(tf_image.get_image())
        self.assertFalse(mock_http_request.called)
        self.assertEqual(mock_http_request.call_count, 0)

    def test_lazy_thumbframes(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)
        mock_http_request.reset_mock()

        # get thumbframes for the first time, which downloads each image
        for counter, tf_image in enumerate(video.get_thumbframes('L2'), start=1):
            self.assertIsNotNone(tf_image.get_image())
            self.assertTrue(mock_http_request.called)
            self.assertEqual(mock_http_request.call_count, counter)

    def test_non_lazy_thumbframes(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)
        mock_http_request.reset_mock()

        # call method in non lazy mode so all images are downloaded right away
        thumbframes = video.get_thumbframes('L2', lazy=False)
        self.assertTrue(mock_http_request.called)
        self.assertEqual(mock_http_request.call_count, len(thumbframes))

        mock_http_request.reset_mock()

        # no additional download here because images are already set
        for tf_image in thumbframes:
            self.assertIsNotNone(tf_image.get_image())
            self.assertFalse(mock_http_request.called)
        self.assertEqual(mock_http_request.call_count, 0)

    # Test that internal _thumbframes dict is set correctly.
    def test_get_thumbframes_info(self, mock_http_request):

        video = YouTubeFrames(self.VIDEO_ID)

        self.assertIsNotNone(video._thumbframes)
        self.assertTrue(video._thumbframes)
        self.assertEqual(len(video._thumbframes), 3)

        for i in range(3):
            tf_id = 'L{}'.format(i)
            self.assertIn(tf_id, video._thumbframes)
            self.assertThumbFrames(video._thumbframes[tf_id])

    def test_thumbframes_formats(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)
        self.assertEqual(len(video.thumbframe_formats), 3)

        self.assertEqual(video.thumbframe_formats[0].format_id, 'L2')
        self.assertEqual(video.thumbframe_formats[0].frame_width, 214)
        self.assertEqual(video.thumbframe_formats[0].frame_height, 90)
        self.assertEqual(video.thumbframe_formats[0].frame_size, 214*90)
        self.assertEqual(video.thumbframe_formats[0].total_frames, 94)
        self.assertEqual(video.thumbframe_formats[0].total_images, 4)

        self.assertEqual(video.thumbframe_formats[1].format_id, 'L1')
        self.assertEqual(video.thumbframe_formats[1].frame_width, 107)
        self.assertEqual(video.thumbframe_formats[1].frame_height, 45)
        self.assertEqual(video.thumbframe_formats[1].frame_size, 107*45)
        self.assertEqual(video.thumbframe_formats[1].total_frames, 94)
        self.assertEqual(video.thumbframe_formats[1].total_images, 1)

        self.assertEqual(video.thumbframe_formats[2].format_id, 'L0')
        self.assertEqual(video.thumbframe_formats[2].frame_width, 48)
        self.assertEqual(video.thumbframe_formats[2].frame_height, 27)
        self.assertEqual(video.thumbframe_formats[2].frame_size, 48*27)
        self.assertEqual(video.thumbframe_formats[2].total_frames, 100)
        self.assertEqual(video.thumbframe_formats[2].total_images, 1)

    def test_get_thumbframes(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)

        # download 1 image from the L0 set
        mock_http_request.reset_mock()
        self.assertThumbFrames(video.get_thumbframes('L0'))
        self.assertEqual(mock_http_request.call_count, 1)

        # download 1 image from the L1 set
        mock_http_request.reset_mock()
        self.assertThumbFrames(video.get_thumbframes('L1'))
        self.assertEqual(mock_http_request.call_count, 1)

        # download 4 images from the L2 set
        mock_http_request.reset_mock()
        self.assertThumbFrames(video.get_thumbframes('L2'))
        self.assertEqual(mock_http_request.call_count, 4)

    def test_get_thumbframes_default_to_best_format(self, mock_http_request):
        video = YouTubeFrames(self.VIDEO_ID)

        default_thumbframes = video.get_thumbframes()
        self.assertThumbFrames(default_thumbframes)

        selected_thumbframes = video.get_thumbframes('L2')
        self.assertThumbFrames(selected_thumbframes)

        self.assertEqual(default_thumbframes, selected_thumbframes)
