from pytubefix import YouTube
from pytubefix.cli import on_progress

url = "https://www.youtube.com/watch?v=lgUFkM34R7U" # paste your YouTube video URL here

video = YouTube(
    proxies={"http": "http://127.0.0.1:8881",
             "https": "http://127.0.0.1:8881"},
    url=url,
    on_progress_callback=on_progress,
)

print('Title:', video.title)

stream = video.streams.get_highest_resolution()
stream.download()