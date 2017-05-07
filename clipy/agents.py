import logging
import urllib.parse

import clipy.models
import clipy.request

from clipy.utils import take_first as tf

logger = logging.getLogger(__name__)


class Agent():
    def __init__(self, lookup=None, vid=None):
        self.lookup = lookup
        self.vid = vid

    async def get_video(self):
        self._load_video_id()
        logger.debug(f'{self.__class__.__name__} get_video "{self.lookup}" --> vid "{self.vid}"')
        data = await self._get_info()
        return clipy.models.VideoModel(self.vid, data)


class YoutubeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _load_video_id(self) -> None:
        if not self.vid:
            if '/watch' in self.lookup:
                parts = urllib.parse.urlsplit(self.lookup)
                info = urllib.parse.parse_qs(parts.query)
                self.vid = tf(info.get('v'))

    async def _get_info(self):
        url = f'https://www.youtube.com/get_video_info?video_id={self.vid}'
        data = await clipy.request.get_text(url)
        info = urllib.parse.parse_qs(data)
        status = tf(info.get('status', None))
        if status == 'ok':
            return info
        else:
            raise ValueError('Invalid video Id "{}" {}'.format(self.vid, info))

    async def get_stream(self, idx):
        data = await self._get_info()
        video = clipy.models.VideoModel(self.vid, data, index=idx)
        return video.stream


class VidmeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        return YoutubeAgent(lookup=url)

    elif 'vid.me' in parts.netloc:
        return VidmeAgent(lookup=url)

    return get_agent(url)


def get_agent(vid: str):
    if len(vid) == 11:
        return YoutubeAgent(vid=vid)

    elif len(vid) == 4:
        return VidmeAgent(vid=vid)
