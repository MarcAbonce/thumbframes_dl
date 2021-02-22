# thumbframes_dl
Download thumbnail frames from a video's progress bar.

When you watch a video on the web, you've probably noticed these thumbnail sized preview frames that are shown when you hover the cursor over the video player's progress bar.  
![Screenshot of a YouTube video with the mouse's cursor hovering over the progress bar at the bottom of the video player.
  The video is playing at minute 2:15, but the cursor is hovering over the minute 5:13.
  Over the cursor there's a thumbnail image showing the frame that will be played at minute 5:13.](docs/img/screenshot.webp)  
© Blender Foundation | [cloud.blender.org/spring](https://cloud.blender.org/films/spring)

When you download the actual images, you'll see that they're actually concatenated in grids containing n*m frames like this:  
![Grid of tiny 10x10 images showing the video's frames at a regular interval.](docs/img/storyboard.webp)  
© Blender Foundation | [cloud.blender.org/spring](https://cloud.blender.org/films/spring)

I refer to this individual frames as thumbframes because I couldn't find a better, less confusing name.  

## How to use
A simple example:  
```python
# Download a video's thumbframes images and save them in the filesystem
# Spring | Blender Animation Studio | CC BY 4.0
from thumbframes_dl import YouTubeFrames


# create YouTubeFrames object containing the methods to get the thumbframes
video = YouTubeFrames('https://www.youtube.com/watch?v=WhWc3b3KhnY')

# iterate all images with thumbframes (there may be more than one)
for i, frames_image in enumerate(video.get_thumbframes()):
    file_content = frames_image.get_image()
    with open(f"{video.video_id}_{i}.{frames_image.mime_type}", "wb") as f:
        f.write(file_content)  # save each image
```

For a couple more examples showing the potential usefulness of thumbframes see the [demos](demos).  
For a more detailed description of the API see the [API documentation](docs/main.md).  
