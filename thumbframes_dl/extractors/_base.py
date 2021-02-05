import abc
from functools import reduce, total_ordering
from typing import Dict, List, Optional, Sequence, Union

from thumbframes_dl.utils import InfoExtractor


class ThumbFramesImage(InfoExtractor):
    """
    Each ThumbFramesImage represents a single image with n_frames frames arranged in a cols*rows grid.
    Note that different images may have different sizes and number of frames even if they're from the same video.
    """

    def __init__(self, url: str, width: int, height: int, cols: int, rows: int, n_frames: int):
        self.url = url
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        self.n_frames = n_frames
        self._image = None  # type: Optional[bytes]

    @property
    def image(self) -> Optional[bytes]:
        if self._image is None:
            self._image = self._download_image(self.url)
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

    def __init__(self, key: Optional[str], thumbframes: List[ThumbFramesImage]):
        self.key = key
        self.frame_width = thumbframes[0].width // thumbframes[0].cols
        self.frame_height = thumbframes[0].height // thumbframes[0].rows
        self.total_frames = reduce(lambda acum, x: acum + x.n_frames, thumbframes, 0)
        self.total_images = len(thumbframes)

    def __hash__(self):
        return hash(self.key)

    @property
    def frame_size(self):
        return self.frame_width * self.frame_height

    def __eq__(self, other):
        return self.frame_size == other.frame_size

    def __lt__(self, other):
        return self.frame_size < other.frame_size

    def __repr__(self):
        return "<%s %s: %s %sx%s frames in %s images>" % (
            self.__class__.__name__, self.key, self.total_frames, self.frame_width, self.frame_height, self.total_images
        )


class WebsiteFrames(abc.ABC, InfoExtractor):
    """
    Represents a video and contains its frames.
    A subclass of this class needs to be implemented for each supported website.
    """

    def __init__(self, video_url: str):
        self._input_url = video_url
        self._validate()
        self._thumbframes = self._get_thumbframes()

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
    def thumbframe_formats(self) -> Sequence[ThumbFramesFormat]:
        """
        Available thumbframe formats for the video. Sorted by highest resolution.
        """
        if isinstance(self._thumbframes, dict):
            return tuple(sorted([ThumbFramesFormat(key, tf_images)
                                 for key, tf_images
                                 in self._thumbframes.items()], reverse=True))
        else:
            return tuple([ThumbFramesFormat(None, self._thumbframes)])

    def get_thumbframe_format(self, key: str) -> Optional[ThumbFramesFormat]:
        """
        Get thumbframe format identified by key.
        Will return None if key is not found in video's thumbframe formats.
        """
        if isinstance(self._thumbframes, dict):
            if key in self._thumbframes:
                return ThumbFramesFormat(key, self._thumbframes[key])
        return None

    @abc.abstractmethod
    def _get_thumbframes(self) -> Union[Dict[str, List[ThumbFramesImage]], List[ThumbFramesImage]]:
        """
        Get all the image's metadata from the video. The actual image files are downloaded later.
        If the page offers more than 1 thumbframe set (for example with different resolutions),
        then this method should return a dict so each set is listed separately. Otherwise, return a list.
        """
        pass

    def get_thumbframes(self, key: Optional[str] = None, lazy=True) -> List[ThumbFramesImage]:
        """
        Get the video's ThumbFramesImages as a list.
        If a webpage has more than one thumbframe format, the key parameter needs to be set so this method
        knows which images to return.
        By default, the images are downloaded lazily until the image property is called for each object.
        If the lazy parameter is set to False, all the images will be downloaded right away.
        """

        # _thumbframes may be a single list or many lists in a dict.
        # If it's the latter, a key needs to be passed to know which images set needs to be returned.
        if isinstance(self._thumbframes, list):
            thumbframes_list = self._thumbframes
        elif isinstance(self._thumbframes, dict):
            if not key:
                key = self.thumbframe_formats[0].key
            thumbframes_list = self._thumbframes.get(key, [])  # type: ignore[arg-type]

        if not lazy:
            # call image property to force downloads
            list(map(lambda img: img.image, thumbframes_list))

        return thumbframes_list

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, self.video_id
        )
