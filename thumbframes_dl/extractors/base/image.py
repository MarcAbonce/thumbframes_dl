from typing import Optional

from youtube_dl.YoutubeDL import YoutubeDL
from youtube_dl.extractor.common import InfoExtractor

from thumbframes_dl.utils import logger


class ThumbFramesImage(InfoExtractor):
    """
    Each ThumbFramesImage represents a single image with n_frames frames arranged in a cols*rows grid.
    Note that different images may have different sizes and number of frames even if they're from the same video.
    """

    def __init__(self, url: str, width: int, height: int, cols: int, rows: int, n_frames: int):
        self.set_downloader(YoutubeDL({'source_address': '0.0.0.0', 'logger': logger}))
        self.url = url
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        self.n_frames = n_frames
        self.mime_type: Optional[str] = None
        self._image: Optional[bytes] = None

    def get_image(self) -> bytes:
        """
        The raw image as bytes.
        Tries to download the image if it hasn't been already downloaded.

        :raises ExtractorError
        """
        if self._image is None:
            resp = self._request_webpage(self.url, self.url, fatal=True)
            raw_image = resp.read()
            self.mime_type = resp.headers.get('Content-Type', '').split(';')[0].split('/')[1]
            self._image = raw_image
        return self._image

    def __repr__(self) -> str:
        return "<%s: %sx%s image in a %sx%s grid>" % (
            self.__class__.__name__, self.width, self.height, self.cols, self.rows
        )
