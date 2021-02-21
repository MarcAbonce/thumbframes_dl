import os
from unittest import mock
from urllib.parse import urlparse, quote


TEST_DIR = os.path.dirname(os.path.realpath(__file__))


# Generate filename for html files in test_assets
def url_to_filename(url):
    filename = quote(url[:url.find('&')].replace('/', '_'))
    if not filename.endswith('.html'):
        filename += '.html'
    return filename


# Patch to mock an HTTP response
def mock_http_response(*args, **kwargs):
    url = args[0]

    headers = {}
    ext = urlparse(url).path.split('.')[-1].lower()
    if ext in ['gif', 'jpg', 'jpeg', 'png', 'webp']:
        headers['Content-Type'] = 'image/{}'.format(ext)
        content = get_empty_image(*args, **kwargs)
    else:
        headers['Content-Type'] = 'text/html; charset=utf-8'
        if kwargs.get('get_empty_html', False):
            content = get_empty_html(*args, **kwargs).encode()
        else:
            content = get_video_html(*args, **kwargs).encode()

    return mock.MagicMock(headers=headers, read=lambda: content)


# Patch to open local webpage instead of downloading it
def get_video_html(url, *args, **kwargs):
    filename = url_to_filename(url)
    full_path = os.path.join(TEST_DIR, 'test_assets', filename)
    with open(full_path) as f:
        return f.read()


# Patch to download webpage with no relevant content
def get_empty_html(*args, **kwargs):
    return "<!DOCTYPE html><html><head></head><body></body></html>"


# Patch to download image with no relevant content
def get_empty_image(*args, **kwargs):
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\tpHYs\x00\x00.#\x00\x00.#\x01x\xa5?v\x00\x00\x00\nIDAT\x08\xd7c0\x05\x00\x007\x006\x0b$FC\x00\x00\x00\x00IEND\xaeB`\x82'  # noqa: E501
