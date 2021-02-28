from setuptools import setup, find_packages


def get_file_contents(filename, break_lines=False):
    with open(filename) as f:
        if break_lines:
            return [line.strip() for line in f.readlines()]
        else:
            return f.read()


def get_version():
    return get_file_contents('thumbframes_dl/version.py').split('=')[1].strip('" \n')


setup(
    name="thumbframes_dl",
    version=get_version(),
    url="https://github.com/MarcAbonce/thumbframes_dl",
    description="Download thumbnail frames from a video's progress bar",
    long_description=get_file_contents('README.md'),
    long_description_content_type="text/markdown",
    keywords="videos, youtube, download, frames, thumbnails, storyboards",
    author="Marc Abonce Seguin",
    license="Unlicense",
    classifiers=[
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries",
        "License :: Public Domain",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    install_requires=get_file_contents('requirements.txt', break_lines=True),
    packages=find_packages(),
)
