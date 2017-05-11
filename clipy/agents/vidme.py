import logging
import urllib.parse

import clipy.agents
import clipy.models
import clipy.request

logger = logging.getLogger(__name__)


class VidmeAgent(clipy.agents.Agent):
    def __init__(self, *args):
        super().__init__(*args)

    async def _get_video(self):
        """
        vid: 'ssEN'
        info: type(dict)
        video: <clipy.models.VideoModel object>
        """
        vid = self._get_video_id()
        info = await self._get_info(vid)
        video = clipy.models.VideoModel(vid, info)
        return video

    def _get_video_id(self) -> None:
        url = self.lookup
        vid = url.rpartition('/')[2] if '/' in url else url
        logger.debug(f'{self.__class__.__name__} using vid "{vid}"')
        return vid

    async def _get_info(self, vid):
        url = f'https://api.vid.me/videoByUrl/{vid}'
        data = await clipy.request.get_json(url)
        return data['video']
        # return data['video']['complete_url']

    def _get_stream(self, video, data, index):
        """
        data::

           {'height': None,
            'type': '720p',
            'uri': 'https://d1wst0behutosd.cloudfront.net/videos/15280893/50222025.mp4?Expires...',
            'version': 12,
            'width': None},
        """
        # class Stream(clipy.models.StreamModel):
        #     def display(self):
        #         dimensions = f'{s.width}x({s.height})' if s.width and s.height else ''
        #         return f'{s.type} {dimensions} v{s.version}'

        def extension():
            parts = urllib.parse.urlsplit(data['uri'])
            return parts.path.partition('.')[2]

        name = video.name or video.title
        width = data.get('width')
        height = data.get('height')
        version = data.get('version')
        dimensions = f'{width}x({height})' if width and height else ''
        user = video.info['user']['username']
        type = data.get('type', '')
        ext = extension()
        filename = f'{user}_{name}-({type}){video.vid}.{ext}'.replace('/', '|')

        data.update(
            display=f'{type} {dimensions} v{version}',
            name=clipy.models.StreamModel.safe_name(filename),
            url=data.get('uri'),
        )
        stream = clipy.models.StreamModel(data, video, index)
        return stream

    def load_video_streams(self, video):
        """
        self = <clipy.agents.VidmeAgent object at 0x7f35787c94e0>
        video = <clipy.models.VideoModel object at 0x7f35787c9518>
        """
        for i, stream_format in enumerate(video.formats):
            stream = self._get_stream(video, stream_format, i)
            video.streams.append(stream)

    def load_video_stream(self, video, stream_index: int):
        i = int(stream_index)
        stream_format = video.formats[i]
        stream = self._get_stream(video, stream_format, i)
        video.stream = stream
