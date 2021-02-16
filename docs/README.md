# thumbframes_dl API
Each website handles thumbframes in a unique way, so for each supported website we need to implement a WebsiteFrames subclass.  
Right now, only YouTube is supported.  

## WebsiteFrames Objects  
Represents a video and contains its frames.  
A subclass of WebsiteFrames needs to be implemented for each supported website.  
Subclasses must implement: [video_id](#video_id), [video_url](#video_url), [_get_thumbframes](#_get_thumbframes).  

#### get\_thumbframes

```python
 | get_thumbframes(format_id: Optional[str] = None, lazy=True) -> List[ThumbFramesImage]
```
Get the video's ThumbFramesImages as a list.  
If a webpage has more than one thumbframe format, the format_id parameter needs to be set so this method
knows which images to return.  
By default, the images are downloaded lazily until the image property is called for each object.  
If the lazy parameter is set to False, all the images will be downloaded right away.  

#### thumbframe\_formats

```python
 | @property
 | thumbframe_formats() -> Sequence[ThumbFramesFormat]
```
Available thumbframe formats for the video. Sorted by highest resolution.

#### get\_thumbframe\_format

```python
 | get_thumbframe_format(format_id: Optional[str]) -> Optional[ThumbFramesFormat]
```
Get thumbframe format identified by format_id.  
Will return None if format_id is not found in video's thumbframe formats.  
If no format_id is passed, this will return the highest resolution thumbframe format.  

#### video\_id
```python
 | @property
 | @abc.abstractmethod
 | video_id() -> str
```
Any unique identifier for the video provided by the website.

#### video\_url
```python
 | @property
 | @abc.abstractmethod
 | video_url() -> str
```
The video's URL.
If possible, this URL should be "normalized" to its most canonical form
and not a URL shortner, mirror, embedding or a URL with unnecessary query parameters.

#### \_get\_thumbframes
```python
 | @abc.abstractmethod
 | _get_thumbframes() -> Union[Dict[str, List[ThumbFramesImage]], List[ThumbFramesImage]]
```
Get all the image's metadata from the video. The actual image files are downloaded later.  
If the page offers more than 1 thumbframe set (for example with different resolutions),
then this method should return a dict so each set is listed separately. Otherwise, return a list.

## ThumbFramesImage Objects

Each ThumbFramesImage represents a single image with n_frames frames arranged in a cols*rows grid.  
Note that different images may have different sizes and number of frames even if they're from the same video.

#### image
```python
 | @property
 | image() -> bytes
```
The raw image as bytes.
Raises a RequestException if download fails.

## ThumbFramesFormat Objects

Basic metadata to show the qualities of each set of ThumbFramesImages.  
Useful when there's more than one list of images per video.  
Can be compared and sorted to get the frames with the highest resolution.  

## ExtractorError Objects  
