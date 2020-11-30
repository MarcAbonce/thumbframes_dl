import os
from urllib.parse import quote


TEST_DIR = os.path.dirname(os.path.realpath(__file__))


# Generate filename for html files in test_assets
def url_to_filename(url):
    filename = quote(url.replace('/', '_'))
    if not filename.endswith('.html'):
        filename += '.html'
    return filename


# Patch to open local webpage instead of downloading it
def get_video_html(url, **kwargs):
    filename = url_to_filename(url)
    full_path = os.path.join(TEST_DIR, 'test_assets', filename)
    with open(full_path) as f:
        return f.read()
