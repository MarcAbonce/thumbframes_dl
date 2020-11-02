import math
import json
import urllib

from .utils import int_or_none, compat_str, try_get, ExtractorError


YOUTUBE_URL = 'https://www.youtube.com'
WEBPAGE_URL = YOUTUBE_URL + '//watch?v={VIDEO_ID}'
INFO_URL = YOUTUBE_URL + '/get_video_info?video_id={VIDEO_ID}&el=detailpage'
THUMBNAIL_URL = 'https://i1.ytimg.com/vi/{VIDEO_ID}/{THUMB_NUMBER}.jpg'


def _parse_json(json_string, video_id, transform_source=None, fatal=True):
    if transform_source:
        json_string = transform_source(json_string)
    try:
        return json.loads(json_string)
    except ValueError as ve:
        errmsg = '%s: Failed to parse JSON ' % video_id
        if fatal:
            raise ExtractorError(errmsg, cause=ve)
        else:
            print(errmsg + str(ve))


def download_page(url):
    with urllib.request.urlopen(url) as response:
        return response.read().decode()


def _get_storyboards(video_id, video_info, video_webpage):
    storyboards = []

    # Try to extract storyboards from video_info
    player_response = video_info.get('player_response', [])
    if len(player_response) > 0 and isinstance(player_response[0], compat_str):
        player_response = _parse_json(
            player_response[0], video_id, fatal=False)
        if player_response and 'storyboards' in player_response:
            sb_spec = [try_get(player_response,
                               lambda x: x['storyboards']['playerStoryboardSpecRenderer']['spec'],
                               compat_str)]
        else:
            sb_spec = []
    else:
        sb_spec = video_info.get('storyboard_spec', [])

    # Try to extract storyboards from video_webpage
    if len(sb_spec) == 0:
        sb_index = video_webpage.find('playerStoryboardSpecRenderer')
        if sb_index != -1:
            sb_spec_renderer = video_webpage[sb_index:]
            sb_str = sb_spec_renderer[sb_spec_renderer.find('{'):sb_spec_renderer.find('}') + 1]
            sb_json = _parse_json(
                sb_str.encode("utf-8").decode("unicode_escape"), video_id, fatal=False)
            sb_spec = [sb_json.get('spec')] if sb_json else []

    # Extract information of each storyboard
    for s in filter(None, sb_spec):
        s_parts = s.split('|')
        base_url = s_parts[0]
        i = 0
        for params in s_parts[1:]:
            storyboard_attrib = params.split('#')
            if len(storyboard_attrib) != 8:
                print('Unable to extract storyboard')
                continue

            frame_width = int_or_none(storyboard_attrib[0])
            frame_height = int_or_none(storyboard_attrib[1])
            total_frames = int_or_none(storyboard_attrib[2])
            cols = int_or_none(storyboard_attrib[3])
            rows = int_or_none(storyboard_attrib[4])
            filename = storyboard_attrib[6]
            sigh = storyboard_attrib[7]

            if frame_width and frame_height and cols and rows and total_frames:
                frames = cols * rows
                width, height = frame_width * cols, frame_height * rows
                n_images = int(math.ceil(total_frames / float(cols * rows)))
            else:
                print('Unable to extract storyboard')
                continue

            storyboards_url = base_url.replace('$L', compat_str(i)) + '&'
            for j in range(n_images):
                url = storyboards_url.replace('$N', filename).replace('$M', compat_str(j)) + 'sigh=' + sigh
                if j == n_images - 1:
                    remaining_frames = total_frames % (cols * rows)
                    if remaining_frames != 0:
                        frames = remaining_frames
                        rows = int(math.ceil(float(remaining_frames) / rows))
                        height = rows * frame_height
                        if rows == 1:
                            cols = remaining_frames
                            width = cols * frame_width

                storyboards.append({
                    'id': 'L' + compat_str(i) + '-M' + compat_str(j),
                    'width': width,
                    'height': height,
                    'cols': cols,
                    'rows': rows,
                    'frames': frames,
                    'url': url
                })
            i += 1

    return storyboards


def gettem(video_id):
    video_webpage = download_page(WEBPAGE_URL.format(VIDEO_ID=video_id))
    video_info = urllib.parse.parse_qs(download_page(INFO_URL.format(VIDEO_ID=video_id)))
    return _get_storyboards(video_id, video_info, video_webpage)
