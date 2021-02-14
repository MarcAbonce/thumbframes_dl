from setuptools import setup


def get_file_contents(filename):
    with open(filename) as f:
        return [line.strip() for line in f.readlines()]


def get_version():
    return get_file_contents('thumbframes_dl/version.py')[0].split('=')[1].strip('" ')


setup(
    name="thumbframes_dl",
    version=get_version(),
    url="https://github.com/MarcAbonce/thumbframes_dl",
    description="Download thumbnail frames from a video's progress bar",
    keywords="videos, youtube, download, frames, thumbnails, storyboards",
    license="Unlicense",
    classifiers=[
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.5"
    ],
    install_requires=get_file_contents('requirements.txt'),
)
