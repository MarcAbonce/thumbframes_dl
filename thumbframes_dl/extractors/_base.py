import abc
from typing import Dict, List, Optional, Union

from thumbframes_dl.utils import logger, InfoExtractor


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
        pass

    @property
    @abc.abstractmethod
    def video_url(self) -> str:
        pass

    @abc.abstractmethod
    def _get_thumbframes(self) -> Union[Dict[str, List[ThumbFramesImage]], List[ThumbFramesImage]]:
        """
        Get information of all the thumbframe images that can be downloaded from the video.
        Each image should be represented by a dict with url and whatever metadata is available.
        If the page offers more than 1 thumbframe set (e.g. with different resolutions) then
        return dict where each set is listed separately. Otherwise, return list with each images's data.
        """
        pass

    def get_thumbframes(self, key: str = None, lazy=True) -> List[ThumbFramesImage]:
        if self._thumbframes is None:
            self._thumbframes = self._get_thumbframes()

        # _thumbframes may be a single list or many lists in a dict.
        # If it's the latter, a key needs to be passed to know which images set needs to be returned.
        if isinstance(self._thumbframes, list):
            thumbframes_list = self._thumbframes
        elif isinstance(self._thumbframes, dict):
            if key:
                thumbframes_list = self._thumbframes.get(key, [])
            else:
                logger.error("get_thumbframes requires key when there's more than one storyboard set")
                return []  # TODO: implement behaviour here

        if not lazy:
            # call image property to force downloads
            list(map(lambda img: img.image, thumbframes_list))

        return thumbframes_list
