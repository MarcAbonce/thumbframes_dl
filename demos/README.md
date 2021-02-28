## Demos

There's a lot of computer vision problems that require processing a massive amount of internet videos. In these cases, the bottleneck is usually not the algorithm itself but instead it's retrieving the videos in the first place.  

Downloading a video's thumbframes may help you solve these problems.  

Of course, in most cases there will be a loss in accuracy because the frames are so small and do not contain every single key frame. However, a video's thumbframes should provide enough information to be representative of a video's content in the general sense.  

Hopefully, this library will help you solve problems that you previously thought of as unfeasible.  


### Generate preview  
```sh
python generate_preview_gif.py
```  
This script generates a tiny GIF with a preview of any YouTube video.  
![A tiny animated image showing a preview of what happens in the actual video.](/docs/img/WhWc3b3KhnY.gif) © Blender Foundation | [cloud.blender.org/spring](https://cloud.blender.org/films/spring)  

### OCR  
```sh
python ocr_demo.py
```  
Takes a video with a ["Space opera" style opening crawl](https://en.wikipedia.org/wiki/Star_Wars_opening_crawl#Origin) and prints its text.  
![A long text in a perspective projection crawling up and away from the user towards the horizon, in a style typical of movies in the Space Opera genre.](/docs/img/starnoirs.png) ©  Saving Throw | [youtu.be/kEVOHhFg_s4](https://www.youtube.com/watch?v=kEVOHhFg_s4)  
