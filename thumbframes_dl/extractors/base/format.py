from functools import reduce, total_ordering
from typing import List, Optional

from .image import ThumbFramesImage


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

    def __hash__(self) -> int:
        return hash(self.format_id)

    @property
    def frame_size(self) -> int:
        return self.frame_width * self.frame_height

    def __eq__(self, other) -> bool:
        if not isinstance(other, ThumbFramesFormat):
            return NotImplemented
        return self.frame_size == other.frame_size

    def __lt__(self, other) -> bool:
        if not isinstance(other, ThumbFramesFormat):
            return NotImplemented
        return self.frame_size < other.frame_size

    def __repr__(self) -> str:
        return "<%s %s: %s %sx%s frames in %s images>" % (
            self.__class__.__name__,
            self.format_id, self.total_frames, self.frame_width, self.frame_height, self.total_images
        )
