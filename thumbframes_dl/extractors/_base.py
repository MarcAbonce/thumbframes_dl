import abc
import json
import re

from requests import get, ConnectionError, HTTPError

from thumbframes_dl import logger
from thumbframes_dl.ytdl_utils.utils import (compiled_regex_type, std_headers,
                                             RegexNotFoundError, NO_DEFAULT,
                                             ExtractorError as YTDLExtractorError)


class ExtractorError(YTDLExtractorError):
    def __init__(self, *args, **kwargs):
        kwargs['expected'] = True
        super(ExtractorError, self).__init__(*args, **kwargs)


class InfoExtractor(object):
    """
    Superclass with helper methods to extract information from webpages.
    """

    def _download(self, url, extra_headers={}):
        try:
            response = get(url, headers={**std_headers, **extra_headers})
            response.raise_for_status()
        except (ConnectionError, HTTPError) as e:
            logger.error('Could not download {url}\n{e}'.format(url=url, e=e))
            return
        return response

    def _download_page(self, *args, **kwargs):
        return self._download(*args, **kwargs).text

    def _download_image(self, *args, **kwargs):
        return self._download(*args, **kwargs).content

    def _parse_json(self, json_string, video_id, transform_source=None, fatal=True):
        if transform_source:
            json_string = transform_source(json_string)
        try:
            return json.loads(json_string)
        except ValueError as ve:
            errmsg = '%s: Failed to parse JSON ' % video_id
            if fatal:
                raise ExtractorError(errmsg, cause=ve)
            else:
                logger.warning(errmsg + str(ve))

    def _search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        RegexNotFoundError, depending on fatal, specifying the field name.
        """
        if isinstance(pattern, (str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj:
                    break

        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            else:
                return mobj.group(group)
        elif default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract %s' % name)


class Storyboard(InfoExtractor):
    """
    Each Storyboard represents a single image file downloaded and its associated metadata.
    Each of these images contains n_frames frames arranged in a cols*rows grid.
    Note that different Storyboard objects may have different sizes and frames even if
    they're from the same video.
    """

    def __init__(self, url, image, width, height, cols, rows, n_frames):
        self.url = url
        self._image = image
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        self.n_frames = n_frames

    @property
    def image(self):
        if self._image is None:
            self._image = self._download_image(self.url)
        return self._image


class StoryboardSet(object):
    """
    Iterator for Storyboards.
    """

    def __init__(self, data):
        self.i = 0
        self._data = data

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= len(self._data):
            raise StopIteration
        sb = self._data[self.i]
        self.i += 1
        return Storyboard(sb['url'],
                          sb.get('image'),
                          sb.get('width'),
                          sb.get('height'),
                          sb.get('cols'),
                          sb.get('rows'),
                          sb.get('n_frames'))


class WebsiteFrames(abc.ABC, InfoExtractor):
    """
    Represents a video and contains its frames.
    A subclass of this class needs to be implemented for each supported website.
    """

    def __init__(self, video_url):
        self._input_url = video_url
        self._validate()
        self._thumbframes_info = self._get_thumbframes_info()

    @abc.abstractmethod
    def _validate(self):
        """
        Method that validates that self._input_url is a valid URL or id for this website.
        If not, an ExtractorError should be thrown here.
        """
        pass

    @property
    @abc.abstractmethod
    def video_id(self):
        pass

    @property
    @abc.abstractmethod
    def video_url(self):
        pass

    @abc.abstractmethod
    def _get_thumbframes_info(self):
        """
        Get information of all the thumbframe images that can be downloaded from the video.
        Each image should be represented by a dict with url and whatever metadata is available.
        If the page offers more than 1 thumbframe set (e.g. with different resolutions) then
        return dict where each set is listed separately. Otherwise, return list with each images's data.
        """
        pass

    def get_thumbframes(self, key=None, lazy=True):
        if self._thumbframes_info is None:
            self._thumbframes_info = self.get_thumbframes_info()

        # Info may be a single list or many lists in a dict.
        # If it's the latter, a key needs to be passed to know which images set needs to be returned.
        if key:
            img_list = self.thumbframes_info.get(key)
        else:
            img_list = self.thumbframes_info

        if img_list:
            if not lazy:
                for img_info in img_list:
                    img_info['image'] = self._download_image(img_info['url'])
            return StoryboardSet(img_list)
