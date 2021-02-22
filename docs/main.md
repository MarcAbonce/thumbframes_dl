# thumbframes_dl API

## WebsiteFrames's Subclasses
Each website handles thumbframes in a unique way, so for each supported website we need to implement a [WebsiteFrames](extractors.md#extractors._base.WebsiteFrames) subclass.  

### YouTubeFrames
YouTube can return thumbframes images in different formats, such as:
* **L0**: A single small image with a 10x10 grid.  
* **L1**: A set of bigger images with a 10x10 grid each.  
* **L2**: A set of bigger images with a 5x5 grid each.  

The image sizes amay vary per video. Also, a video doesn't necessarily contain images in all the formats.  

## ExtractorError Objects  
ExtractorError is [youtube_dl](https://github.com/ytdl-org/youtube-dl)'s main Exception class.  
The thumbframes_dl library mostly relies on youtube_dl to handle downloads, parsing and validations, so this is the main Exception that you would need to catch if anything fails.  
You can import it directly from `thumbframes_dl`.
