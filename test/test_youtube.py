import re
import os
import logging
import unittest

import httpretty  # type: ignore

from numbers import Number
from urllib.parse import urlparse

from youtube_dl.utils import ExtractorError
from thumbframes_dl import YouTubeFrames


TEST_DIR = os.path.dirname(os.path.realpath(__file__))


class TestYouTubeFrames(unittest.TestCase):

    # Spring | Blender Animation Studio | CC BY 4.0
    VIDEO_ID = 'WhWc3b3KhnY'
    VIDEO_URL = 'https://www.youtube.com/watch?v=WhWc3b3KhnY'

    # Mock YoutubeDL's internal HTTP requests
    def setUp(self):
        logging.disable(logging.CRITICAL)  # comment out if needed for debugging a failed test

        httpretty.reset()
        httpretty.enable(allow_net_connect=False)

        # main video page
        video_path = 'www_youtube_com_WhWc3b3KhnY.html'
        with open(os.path.join(TEST_DIR, 'test_assets', video_path)) as f:
            video_page = f.read()
        httpretty.register_uri(
            httpretty.GET,
            self.VIDEO_URL,
            body=video_page
        )

        # file with video data
        details_path = 'www_youtube_com_get_video_info_WhWc3b3KhnY_detailpage.html'
        with open(os.path.join(TEST_DIR, 'test_assets', details_path)) as f:
            details_page = f.read()
        httpretty.register_uri(
            httpretty.POST,
            'https://www.youtube.com/youtubei/v1/player',
            body=details_page
        )

        # images
        httpretty.register_uri(
            httpretty.GET,
            re.compile('^.*(jpg|jpeg|webp|png|gif)$'),
            body=(b'RIFF$\x00\x00\x00WEBPVP8 '
                  b'\x18\x00\x00\x000\x01\x00\x9d\x01*'
                  b'\x01\x00\x01\x00\x0f\xc0\xfe%\xa4\x00\x03p\x00\xfe\xe6\xb5\x00\x00'),
            forcing_headers={'Content-Type': 'image/webp'}
        )

    def tearDown(self):
        httpretty.disable()
        logging.disable(logging.NOTSET)

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

    def test_init_with_video_id(self):
        video = YouTubeFrames(self.VIDEO_ID)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_init_with_video_url(self):
        video = YouTubeFrames(self.VIDEO_URL)
        self.assertEqual(video.video_id, self.VIDEO_ID)
        self.assertEqual(video.video_url, self.VIDEO_URL)

    def test_fail_init_with_bad_url(self):
        BAD_URL = 'BAD_URL'
        with self.assertRaises(ExtractorError):
            _ = YouTubeFrames(BAD_URL)

    def test_thumbframes_not_found(self):
        # mock responses with no thumbframes
        httpretty.reset()
        httpretty.register_uri(
            httpretty.GET,
            re.compile('.*'),
            body='<!DOCTYPE html><html><head></head><body></body></html>'
        )
        httpretty.register_uri(
            httpretty.POST,
            re.compile('.*'),
            body='{}'
        )

        # this represents a valid YouTube video that returns no thumbframes
        video = YouTubeFrames('ZERO_THUMBS')

        # number of HTTP requests that YouTubeDL tries at first
        # it's set as a variable in case lib changes internally
        number_of_requests = len(httpretty.latest_requests())

        # thumbframes info is an empty structure but NOT a None
        self.assertIsNotNone(video._thumbframes)
        self.assertEqual(len(video.get_thumbframes()), 0)

        # thumbframe formats methods shouldn't break
        self.assertIsNone(video.thumbframe_formats)
        self.assertIsNone(video.get_thumbframe_format())

        # should NOT re-try download even if thumbframes info is empty
        self.assertEqual(len(httpretty.latest_requests()), number_of_requests)

    def test_page_only_downloads_once(self):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads page with frames info
        self.assertIsNotNone(video.get_thumbframes('L0'))
        self.assertEqual(len(httpretty.latest_requests()), 1)

        # should NOT download again if thumbframes data has already been obtained before
        self.assertIsNotNone(video.get_thumbframes('L1'))
        self.assertEqual(len(httpretty.latest_requests()), 1)

    def test_images_only_download_once(self):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads each image
        thumbframes = video.get_thumbframes('L2')
        for tf_image in video.get_thumbframes('L2'):
            self.assertIsNotNone(tf_image.get_image())
        self.assertEqual(len(httpretty.latest_requests()), len(thumbframes) + 1)

        # should NOT download images again if they have already been downloaded before
        same_thumbframes_as_before = video.get_thumbframes('L2')
        for tf_image in same_thumbframes_as_before:
            self.assertIsNotNone(tf_image.get_image())
        self.assertEqual(len(httpretty.latest_requests()), len(thumbframes) + 1)

    def test_lazy_thumbframes(self):
        video = YouTubeFrames(self.VIDEO_ID)

        # get thumbframes for the first time, which downloads each image
        for counter, tf_image in enumerate(video.get_thumbframes('L2'), start=1):
            self.assertIsNotNone(tf_image.get_image())
            self.assertEqual(len(httpretty.latest_requests()), counter + 1)

    def test_non_lazy_thumbframes(self):
        video = YouTubeFrames(self.VIDEO_ID)

        # call method in non lazy mode so all images are downloaded right away
        thumbframes = video.get_thumbframes('L2', lazy=False)
        self.assertEqual(len(httpretty.latest_requests()), len(thumbframes) + 1)

        # no additional download here because images are already set
        for tf_image in thumbframes:
            self.assertIsNotNone(tf_image.get_image())
        self.assertEqual(len(httpretty.latest_requests()), len(thumbframes) + 1)

    # Test that internal _thumbframes dict is set correctly.
    def test_get_thumbframes_info(self):

        video = YouTubeFrames(self.VIDEO_ID)

        self.assertIsNotNone(video._thumbframes)
        self.assertTrue(video._thumbframes)
        self.assertEqual(len(video._thumbframes), 3)

        for i in range(3):
            tf_id = 'L{}'.format(i)
            self.assertIn(tf_id, video._thumbframes)
            self.assertThumbFrames(video._thumbframes[tf_id])

    def test_thumbframes_formats(self):
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

    def test_get_thumbframes_default_to_best_format(self):
        video = YouTubeFrames(self.VIDEO_ID)

        default_thumbframes = video.get_thumbframes()
        self.assertThumbFrames(default_thumbframes)

        selected_thumbframes = video.get_thumbframes('L2')
        self.assertThumbFrames(selected_thumbframes)

        self.assertEqual(default_thumbframes, selected_thumbframes)
