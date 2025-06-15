# Table of Contents

* [WebsiteFrames](#thumbframes_dl.extractors.base.frames.WebsiteFrames)
    * [video\_id](#thumbframes_dl.extractors.base.frames.WebsiteFrames.video_id)
    * [video\_url](#thumbframes_dl.extractors.base.frames.WebsiteFrames.video_url)
    * [thumbframe\_formats](#thumbframes_dl.extractors.base.frames.WebsiteFrames.thumbframe_formats)
    * [get\_thumbframe\_format](#thumbframes_dl.extractors.base.frames.WebsiteFrames.get_thumbframe_format)
    * [download\_thumbframe\_info](#thumbframes_dl.extractors.base.frames.WebsiteFrames.download_thumbframe_info)
    * [get\_thumbframes](#thumbframes_dl.extractors.base.frames.WebsiteFrames.get_thumbframes)
* [ThumbFramesImage](#thumbframes_dl.extractors.base.image.ThumbFramesImage)
    * [get\_image](#thumbframes_dl.extractors.base.image.ThumbFramesImage.get_image)
* [ThumbFramesFormat](#thumbframes_dl.extractors.base.format.ThumbFramesFormat)


<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames"></a>

## WebsiteFrames Objects

```python
class WebsiteFrames(abc.ABC, InfoExtractor)
```

Represents a video and contains its frames.
A subclass of this class needs to be implemented for each supported website.

<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames.video_id"></a>

#### video\_id

```python
@property
@abc.abstractmethod
def video_id() -> str
```

Any unique identifier for the video provided by the website.

<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames.video_url"></a>

#### video\_url

```python
@property
@abc.abstractmethod
def video_url() -> str
```

The video's URL.
If possible, this URL should be "normalized" to its most canonical form
and not a URL shortener, mirror, embedding or a URL with unnecessary query parameters.

<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames.thumbframe_formats"></a>

#### thumbframe\_formats

```python
@property
def thumbframe_formats() -> Optional[Sequence[ThumbFramesFormat]]
```

Available thumbframe formats for the video. Sorted by highest resolution.

<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames.get_thumbframe_format"></a>

#### get\_thumbframe\_format

```python
def get_thumbframe_format(
        format_id: Optional[str] = None) -> Optional[ThumbFramesFormat]
```

Get thumbframe format identified by format_id.
Will return None if format_id is not found in video's thumbframe formats.
If no format_id is passed, this will return the highest resolution thumbframe format.

<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames.download_thumbframe_info"></a>

#### download\_thumbframe\_info

```python
@abc.abstractmethod
def download_thumbframe_info(
) -> Union[dict[str, list[ThumbFramesImage]], list[ThumbFramesImage]]
```

Get all the thumbframe's metadata from the video. The actual image files are downloaded later.
If the page offers more than 1 thumbframe set (for example with different resolutions),
then this method should return a dict so each set is listed separately. Otherwise, return a list.

<a id="thumbframes_dl.extractors.base.frames.WebsiteFrames.get_thumbframes"></a>

#### get\_thumbframes

```python
def get_thumbframes(format_id: Optional[str] = None,
                    lazy=True) -> list[ThumbFramesImage]
```

Get the video's ThumbFramesImages as a list.
If a webpage has more than one thumbframe format, the format_id parameter needs to be set so this method
knows which images to return.
By default, the images are downloaded lazily until the image property is called for each object.
If the lazy parameter is set to False, all the images will be downloaded right away.

<a id="thumbframes_dl.extractors.base.image.ThumbFramesImage"></a>

## ThumbFramesImage Objects

```python
class ThumbFramesImage(InfoExtractor)
```

Each ThumbFramesImage represents a single image with n_frames frames arranged in a cols*rows grid.
Note that different images may have different sizes and number of frames even if they're from the same video.

<a id="thumbframes_dl.extractors.base.image.ThumbFramesImage.get_image"></a>

#### get\_image

```python
def get_image() -> bytes
```

The raw image as bytes.

Tries to download the image if it hasn't been already downloaded.

:raises ExtractorError

<a id="thumbframes_dl.extractors.base.format.ThumbFramesFormat"></a>

## ThumbFramesFormat Objects

```python
@total_ordering
class ThumbFramesFormat(object)
```

Basic metadata to show the qualities of each set of ThumbFramesImages.
Useful when there's more than one list of images per video.
Can be compared and sorted to get the frames with the highest resolution.

