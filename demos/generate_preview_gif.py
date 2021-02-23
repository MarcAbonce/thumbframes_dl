"""
This script generates a tiny GIF with a preview of any YouTube video.
"""
from sys import path
from os.path import realpath, dirname
path.append(realpath(dirname(realpath(__file__)) + '/../'))

from io import BytesIO
from PIL import Image
from thumbframes_dl import YouTubeFrames

# Spring | Blender Animation Studio | CC BY 4.0
VIDEO_URL = 'https://www.youtube.com/watch?v=WhWc3b3KhnY'
THUMBFRAME_FORMAT_ID = 'L2'


if __name__ == "__main__":
    # create YouTubeFrames object containing the methods to get the thumbframes
    video = YouTubeFrames(VIDEO_URL)

    # get an object that contains some useful metadata about the thumbframes
    # YouTube offers different thumbframe sets with different qualities
    frames_format = video.get_thumbframe_format(THUMBFRAME_FORMAT_ID)
    if frames_format is None:
        print("Video {} doesn't have thumbframes on the size I wanted to create a preview.".format(video.video_id))
        exit()

    frames = []
    for frames_image in video.get_thumbframes(THUMBFRAME_FORMAT_ID):
        # open image that contains the thumbframes
        image = Image.open(BytesIO(frames_image.get_image()))

        # iterate each thumbframe in the image, crop the thumbframe and append it to the frames list
        for row in range(frames_image.rows):
            for col in range(frames_image.cols):
                frames.append(image.crop((
                    col*frames_format.frame_width,
                    row*frames_format.frame_height,
                    (col + 1)*frames_format.frame_width,
                    (row + 1)*frames_format.frame_height
                )))

    # create a new gif image from the frames list
    gif = Image.new(mode='RGB', size=(frames_format.frame_width, frames_format.frame_height))
    gif.save(fp='{}.gif'.format(video.video_id), format='GIF',
             append_images=frames,
             save_all=True, duration=1000, loop=0)
