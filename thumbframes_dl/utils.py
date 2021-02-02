import json
import logging
import re
from typing import Dict, Optional

from requests import get, ConnectionError, HTTPError, Response

from thumbframes_dl.ytdl_utils.utils import (compiled_regex_type, std_headers,
                                             RegexNotFoundError, NO_DEFAULT,
                                             ExtractorError as YTDLExtractorError)


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ExtractorError(YTDLExtractorError):
    def __init__(self, *args, **kwargs):
        kwargs['expected'] = True
        super(ExtractorError, self).__init__(*args, **kwargs)


class InfoExtractor(object):
    """
    Superclass with helper methods to extract information from webpages.
    """

    def _download(self, url: str, extra_headers: Dict[str, str] = {}) -> Optional[Response]:
        try:
            response = get(url, headers={**std_headers, **extra_headers})
            response.raise_for_status()
        except (ConnectionError, HTTPError) as e:
            logger.error('Could not download {url}\n{e}'.format(url=url, e=e))
            return None
        return response

    def _download_page(self, *args, **kwargs) -> Optional[str]:
        response = self._download(*args, **kwargs)
        if response:
            return response.text
        return None

    def _download_image(self, *args, **kwargs) -> Optional[bytes]:
        response = self._download(*args, **kwargs)
        if response:
            return response.content
        return None

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
