# Table of Contents

* [extractors.\_base](#extractors._base)
  * [ThumbFramesImage](#extractors._base.ThumbFramesImage)
    * [get\_image](#extractors._base.ThumbFramesImage.get_image)
  * [ThumbFramesFormat](#extractors._base.ThumbFramesFormat)
  * [WebsiteFrames](#extractors._base.WebsiteFrames)
    * [video\_id](#extractors._base.WebsiteFrames.video_id)
    * [video\_url](#extractors._base.WebsiteFrames.video_url)
    * [thumbframe\_formats](#extractors._base.WebsiteFrames.thumbframe_formats)
    * [get\_thumbframe\_format](#extractors._base.WebsiteFrames.get_thumbframe_format)
    * [download\_thumbframe\_info](#extractors._base.WebsiteFrames.download_thumbframe_info)
    * [get\_thumbframes](#extractors._base.WebsiteFrames.get_thumbframes)

<a name="extractors._base"></a>
# extractors.\_base

<a name="extractors._base.ThumbFramesImage"></a>
## ThumbFramesImage Objects

```python
class ThumbFramesImage(InfoExtractor)
```

Each ThumbFramesImage represents a single image with n_frames frames arranged in a cols*rows grid.
Note that different images may have different sizes and number of frames even if they're from the same video.

<a name="extractors._base.ThumbFramesImage.get_image"></a>
#### get\_image

```python
 | get_image() -> bytes
```

The raw image as bytes.
Raises an ExtractorError if download fails.

<a name="extractors._base.ThumbFramesFormat"></a>
## ThumbFramesFormat Objects

```python
@total_ordering
class ThumbFramesFormat(object)
```

Basic metadata to show the qualities of each set of ThumbFramesImages.
Useful when there's more than one list of images per video.
Can be compared and sorted to get the frames with the highest resolution.

<a name="extractors._base.WebsiteFrames"></a>
## WebsiteFrames Objects

```python
class WebsiteFrames(abc.ABC,  InfoExtractor)
```

Represents a video and contains its frames.
A subclass of this class needs to be implemented for each supported website.

<a name="extractors._base.WebsiteFrames.video_id"></a>
#### video\_id

```python
 | @property
 | @abc.abstractmethod
 | video_id() -> str
```

Any unique identifier for the video provided by the website.

<a name="extractors._base.WebsiteFrames.video_url"></a>
#### video\_url

```python
 | @property
 | @abc.abstractmethod
 | video_url() -> str
```

The video's URL.
If possible, this URL should be "normalized" to its most canonical form
and not a URL shortner, mirror, embedding or a URL with unnecessary query parameters.

<a name="extractors._base.WebsiteFrames.thumbframe_formats"></a>
#### thumbframe\_formats

```python
 | @property
 | thumbframe_formats() -> Optional[Sequence[ThumbFramesFormat]]
```

Available thumbframe formats for the video. Sorted by highest resolution.

<a name="extractors._base.WebsiteFrames.get_thumbframe_format"></a>
#### get\_thumbframe\_format

```python
 | get_thumbframe_format(format_id: Optional[str] = None) -> Optional[ThumbFramesFormat]
```

Get thumbframe format identified by format_id.
Will return None if format_id is not found in video's thumbframe formats.
If no format_id is passed, this will return the highest resolution thumbframe format.

<a name="extractors._base.WebsiteFrames.download_thumbframe_info"></a>
#### download\_thumbframe\_info

```python
 | @abc.abstractmethod
 | download_thumbframe_info() -> Union[Dict[str, List[ThumbFramesImage]], List[ThumbFramesImage]]
```

Get all the thumbframe's metadata from the video. The actual image files are downloaded later.
If the page offers more than 1 thumbframe set (for example with different resolutions),
then this method should return a dict so each set is listed separately. Otherwise, return a list.

<a name="extractors._base.WebsiteFrames.get_thumbframes"></a>
#### get\_thumbframes

```python
 | get_thumbframes(format_id: Optional[str] = None, lazy=True) -> List[ThumbFramesImage]
```

Get the video's ThumbFramesImages as a list.
If a webpage has more than one thumbframe format, the format_id parameter needs to be set so this method
knows which images to return.
By default, the images are downloaded lazily until the image property is called for each object.
If the lazy parameter is set to False, all the images will be downloaded right away.
