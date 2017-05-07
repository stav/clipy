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
        info = urllib.parse.parse_qs(data)
        status = tf(info.get('status', None))
        if status == 'ok':
            return info
        else:
            raise ValueError('Invalid video Id "{}" {}'.format(vid, info))

    async def get_stream(self, idx):
        video = await self._get_video()
        self._load_video_stream(video, idx)
        return video.stream

    def _get_stream(self, video, string, index):
        data = {k: tf(v) for k, v in urllib.parse.parse_qs(string).items()}
        itag = data.get('itag', None)
        data.update(
            resolution=clipy.youtube.get_resolution(itag),
            extension=clipy.youtube.get_extension(itag),
            title=video.info.get('title', '<NOTITLE>'),
        )
        return clipy.models.StreamModel(data, video, index)

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

    def _load_video_id(self) -> None:
        if not self.vid:
            url = self.lookup
            self.vid = url.rpartition('/')[2] if '/' in url else url

    async def _get_info(self):
        url = f'https://api.vid.me/videoByUrl/{self.vid}'
        data = await clipy.request.get_json(url)
        # import pprint
        # data = pprint.pformat(data)
        # logger.debug(f'get_video data: {data}')
        return data['video']
        # return data['video']['complete_url']


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
