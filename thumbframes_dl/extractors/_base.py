import abc
from functools import reduce, total_ordering
from typing import Dict, List, Optional, Sequence, Union

from youtube_dl.YoutubeDL import YoutubeDL
from youtube_dl.extractor.common import InfoExtractor

from thumbframes_dl.utils import logger


class ThumbFramesImage(InfoExtractor):
    """
    Each ThumbFramesImage represents a single image with n_frames frames arranged in a cols*rows grid.
    Note that different images may have different sizes and number of frames even if they're from the same video.
    """

    def __init__(self, url: str, width: int, height: int, cols: int, rows: int, n_frames: int):
        self.set_downloader(YoutubeDL({'logger': logger}))
        self.url = url
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        self.n_frames = n_frames
        self.mime_type = None
        self._image = None  # type: Optional[bytes]

    def get_image(self) -> bytes:
        """
        The raw image as bytes.
        Raises an ExtractorError if download fails.
        """
        if self._image is None:
            resp = self._request_webpage(self.url, self.url, fatal=True)
            raw_image = resp.read()
            self.mime_type = resp.headers.get('Content-Type', '').split(';')[0].split('/')[1]
            self._image = raw_image
        return self._image

    def __repr__(self):
        return "<%s: %sx%s image in a %sx%s grid>" % (
            self.__class__.__name__, self.width, self.height, self.cols, self.rows
        )


@total_ordering
class ThumbFramesFormat(object):
    """
    Basic metadata to show the qualities of each set of ThumbFramesImages.
    Useful when there's more than one list of images per video.
    Can be compared and sorted to get the frames with the highest resolution.
    """

    def __init__(self, format_id: Optional[str], thumbframes: List[ThumbFramesImage]):
        self.format_id = format_id
        self.frame_width = thumbframes[0].width // thumbframes[0].cols
        self.frame_height = thumbframes[0].height // thumbframes[0].rows
        self.total_frames = reduce(lambda acum, x: acum + x.n_frames, thumbframes, 0)
        self.total_images = len(thumbframes)

    def __hash__(self):
        return hash(self.format_id)

    @property
    def frame_size(self):
        return self.frame_width * self.frame_height

    def __eq__(self, other):
        return self.frame_size == other.frame_size

    def __lt__(self, other):
        return self.frame_size < other.frame_size

    def __repr__(self):
        return "<%s %s: %s %sx%s frames in %s images>" % (
            self.__class__.__name__,
            self.format_id, self.total_frames, self.frame_width, self.frame_height, self.total_images
        )


class WebsiteFrames(abc.ABC, InfoExtractor):
    """
    Represents a video and contains its frames.
    A subclass of this class needs to be implemented for each supported website.
    """

    def __init__(self, video_url: str):
        self.set_downloader(YoutubeDL({'logger': logger}))
        self._input_url = video_url
        self._validate()
        self._thumbframes = self.download_thumbframe_info()

    @abc.abstractmethod
    def _validate(self) -> None:
        """
        Method that validates that self._input_url is a valid URL or id for this website.
        If not, an ExtractorError should be thrown here.
        """
        pass

    @property
    @abc.abstractmethod
    def video_id(self) -> str:
        """
        Any unique identifier for the video provided by the website.
        """
        pass

    @property
    @abc.abstractmethod
    def video_url(self) -> str:
        """
        The video's URL.
        If possible, this URL should be "normalized" to its most canonical form
        and not a URL shortner, mirror, embedding or a URL with unnecessary query parameters.
        """
        pass

    @property
    def thumbframe_formats(self) -> Optional[Sequence[ThumbFramesFormat]]:
        """
        Available thumbframe formats for the video. Sorted by highest resolution.
        """
        if len(self._thumbframes) == 0:
            return None

        if isinstance(self._thumbframes, dict):
            return tuple(sorted([ThumbFramesFormat(format_id, tf_images)
                                 for format_id, tf_images
                                 in self._thumbframes.items()], reverse=True))
        else:
            return tuple([ThumbFramesFormat(None, self._thumbframes)])

    def get_thumbframe_format(self, format_id: Optional[str] = None) -> Optional[ThumbFramesFormat]:
        """
        Get thumbframe format identified by format_id.
        Will return None if format_id is not found in video's thumbframe formats.
        If no format_id is passed, this will return the highest resolution thumbframe format.
        """
        if self.thumbframe_formats is None:
            return None

        if isinstance(self._thumbframes, list):
            return ThumbFramesFormat(None, self._thumbframes)
        elif isinstance(self._thumbframes, dict):
            if format_id is None:
                return self.thumbframe_formats[0]
            elif format_id in self._thumbframes:
                return ThumbFramesFormat(format_id, self._thumbframes[format_id])
        return None

    @abc.abstractmethod
    def download_thumbframe_info(self) -> Union[Dict[str, List[ThumbFramesImage]], List[ThumbFramesImage]]:
        """
        Get all the thumbframe's metadata from the video. The actual image files are downloaded later.
        If the page offers more than 1 thumbframe set (for example with different resolutions),
        then this method should return a dict so each set is listed separately. Otherwise, return a list.
        """
        pass

    def get_thumbframes(self, format_id: Optional[str] = None, lazy=True) -> List[ThumbFramesImage]:
        """
        Get the video's ThumbFramesImages as a list.
        If a webpage has more than one thumbframe format, the format_id parameter needs to be set so this method
        knows which images to return.
        By default, the images are downloaded lazily until the image property is called for each object.
        If the lazy parameter is set to False, all the images will be downloaded right away.
        """

        # _thumbframes may be a single list or many lists in a dict.
        # If it's the latter, a format_id needs to be passed to know which images set needs to be returned.
        if isinstance(self._thumbframes, list):
            thumbframes_list = self._thumbframes
        elif isinstance(self._thumbframes, dict):
            if not format_id and self.thumbframe_formats:
                format_id = self.thumbframe_formats[0].format_id
            thumbframes_list = self._thumbframes.get(format_id, [])  # type: ignore[arg-type]

        if not lazy:
            # call image property to force downloads
            list(map(lambda img: img.get_image(), thumbframes_list))

        return thumbframes_list

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, self.video_id
        )
