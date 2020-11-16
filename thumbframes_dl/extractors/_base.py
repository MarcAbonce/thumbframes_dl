import abc
import json
import re

from requests import get, ConnectionError, HTTPError

from thumbframes_dl import logger
from thumbframes_dl.ytdl_utils.utils import (compiled_regex_type, std_headers,
                                             ExtractorError, RegexNotFoundError, NO_DEFAULT)


class InfoExtractor(abc.ABC):

    def __init__(self, video_url, lazy=False):
        self.video_url = video_url
        self._thumbframes = None
        self.errors = []
        if not lazy:
            self._thumbframes = self.thumbframes

    @property
    def thumbframes(self):
        if self._thumbframes is None:
            self._thumbframes = self._get_thumbframes()
        return self._thumbframes

    @abc.abstractmethod
    def _get_thumbframes(self):
        pass

    def _download_page(self, url, extra_headers={}):
        try:
            response = get(url, headers={**std_headers, **extra_headers})
            response.raise_for_status()
        except (ConnectionError, HTTPError) as e:
            logger.error('Could not download {url}\n{e}'.format(url=url, e=e))
            return
        return response.text

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
