
class Agent():
    def __init__(self, lookup):
        self.lookup = lookup

    async def get_video(self):
        video = await self._get_video()
        self.load_video_streams(video)
        return video

    async def get_stream(self, idx):
        video = await self._get_video()
        self.load_video_stream(video, idx)
        return video.stream
