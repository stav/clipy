import logging
import urllib.parse

import clipy.models
import clipy.request
import clipy.youtube

from clipy.utils import take_first as tf

logger = logging.getLogger(__name__)


class Agent():
    def __init__(self, lookup):
        self.lookup = lookup

    async def get_video(self):
        video = await self._get_video()
        self._load_video_streams(video)
        return video

    async def get_stream(self, idx):
        video = await self._get_video()
        self._load_video_stream(video, idx)
        return video.stream


class YoutubeAgent(Agent):
    def __init__(self, *args):
        super().__init__(*args)

    async def _get_video(self):
        vid = self._get_video_id()
        info = await self._get_info(vid)
        video = clipy.models.VideoModel(vid, info)
        video.info_map = dict(
            videoid='video_id',
            duration='length_seconds',
        )
        return video

    def _get_video_id(self) -> None:
        if '/watch' in self.lookup:
            parts = urllib.parse.urlsplit(self.lookup)
            info = urllib.parse.parse_qs(parts.query)
            vid = tf(info.get('v'))
            logger.debug(f'{self.__class__.__name__} "{self.lookup}" --> vid "{vid}"')
            return vid

        logger.debug(f'{self.__class__.__name__} using vid "{self.lookup}"')
        return self.lookup

    async def _get_info(self, vid):
        url = f'https://www.youtube.com/get_video_info?video_id={vid}'
        data = await clipy.request.get_text(url)
        info = {k: tf(v) for k, v in urllib.parse.parse_qs(data).items()}
        if info.get('status') == 'ok':
            return info
        else:
            raise ValueError(f'Invalid video Id "{vid}" {info}')

    def _get_stream(self, video, string, index):
        name = video.name or video.title
        data = {k: tf(v) for k, v in urllib.parse.parse_qs(string).items()}
        quality = data.get('quality', '')
        type = data.get('type', '')
        itag = data.get('itag')
        itags = clipy.youtube.get_itags(itag)
        res = clipy.youtube.get_resolution(itag)
        ext = clipy.youtube.get_extension(itag)
        author = video.info.get('author')

        data.update(
            display=f'{itags} {quality} ({res}) {type}',
            title=video.info.get('title', name),
            name=f'{author}_{name}-({res}){video.vid}.{ext}'.replace('/', '|'),
        )
        stream = clipy.models.StreamModel(data, video, index)
        return stream

    def _load_video_streams(self, video):
        if video.info is not None:
            # first we split the mapping on the commas
            stream_map = clipy.youtube.get_stream_map(video.info)
            # collect all streams data since we don't have a stream index
            for i, string in enumerate(stream_map):
                stream = self._get_stream(video, string, i)
                video.streams.append(stream)

    def _load_video_stream(self, video, index):
        if video.info is not None:
            # first we split the mapping on the commas
            stream_map = clipy.youtube.get_stream_map(video.info)
            # Just collect the stream we want
            string = stream_map[int(index)]
            video.stream = self._get_stream(video, string, int(index))


class VidmeAgent(Agent):
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
        # import pprint
        # data = pprint.pformat(data)
        # logger.debug(f'get_video data: {data}')
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

        data.update(
            display=f'{type} {dimensions} v{version}',
            name=f'{user}_{name}-({type}){video.vid}.{ext}'.replace('/', '|'),
            url=data.get('uri'),
        )
        stream = clipy.models.StreamModel(data, video, index)
        return stream

    def _load_video_streams(self, video):
        """
        self = <clipy.agents.VidmeAgent object at 0x7f35787c94e0>
        video = <clipy.models.VideoModel object at 0x7f35787c9518>
        """
        for i, stream_format in enumerate(video.formats):
            stream = self._get_stream(video, stream_format, i)
            video.streams.append(stream)

    def _load_video_stream(self, video, stream_index: int):
        i = int(stream_index)
        stream_format = video.formats[i]
        stream = self._get_stream(video, stream_format, i)
        video.stream = stream


def lookup_agent(url: str):
    parts = urllib.parse.urlsplit(url)

    if 'youtube' in parts.netloc:
        return YoutubeAgent(url)

    elif 'vid.me' in parts.netloc:
        return VidmeAgent(url)

    return get_agent(url)


def get_agent(vid: str):
    if len(vid) == 11:
        return YoutubeAgent(vid)

    elif len(vid) == 4:
        return VidmeAgent(vid)
