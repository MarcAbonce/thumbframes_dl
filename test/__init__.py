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
def mock_urlopen(*args, **kwargs):
    url = args[0]
    headers = {}
    ext = urlparse(url).path.split('.')[-1].lower()
    if ext in ['gif', 'jpg', 'jpeg', 'png', 'webp']:
        return mock_empty_image_response(*args, **kwargs)
    else:
        headers['Content-Type'] = 'text/html; charset=utf-8'
        content = get_video_html(*args, **kwargs).encode()

    return mock.MagicMock(status=200, headers=headers, read=lambda: content)


# Patch to open local webpage instead of downloading it
def get_video_html(url, *args, **kwargs):
    filename = url_to_filename(url)
    full_path = os.path.join(TEST_DIR, 'test_assets', filename)
    with open(full_path) as f:
        return f.read()


def mock_empty_html_response(*args, **kwargs):
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    content = "<!DOCTYPE html><html><head></head><body></body></html>"
    return mock.MagicMock(status=200, headers=headers, read=lambda: content.encode())


def mock_empty_json_response(*args, **kwargs):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    content = "{}"
    return mock.MagicMock(status=200, headers=headers, read=lambda: content.encode())


def mock_empty_image_response(*args, **kwargs):
    headers = {'Content-Type': 'image/webp'}
    content = (b'RIFF$\x00\x00\x00WEBPVP8 '
               b'\x18\x00\x00\x000\x01\x00\x9d\x01*\x01\x00\x01\x00\x0f\xc0\xfe%\xa4\x00\x03p\x00\xfe\xe6\xb5\x00\x00')
    return mock.MagicMock(status=200, headers=headers, read=lambda: content)
