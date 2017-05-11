import logging
import urllib.parse

import clipy.agents
import clipy.models
import clipy.request

from clipy.utils import take_first as tf

logger = logging.getLogger(__name__)


class YoutubeAgent(clipy.agents.Agent):
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
        itags = _get_itags(itag)
        res = _get_resolution(itag)
        ext = _get_extension(itag)
        author = video.info.get('author')
        filename = f'{author}_{name}-({res}){video.vid}.{ext}'.replace('/', '|')

        data.update(
            display=f'{itags} {quality} ({res}) {type}',
            title=video.info.get('title', name),
            name=clipy.models.StreamModel.safe_name(filename),
        )
        stream = clipy.models.StreamModel(data, video, index)
        return stream

    def load_video_streams(self, video):
        if video.info is not None:
            # first we split the mapping on the commas
            stream_map = _get_stream_map(video.info)
            # collect all streams data since we don't have a stream index
            for i, string in enumerate(stream_map):
                stream = self._get_stream(video, string, i)
                video.streams.append(stream)

    def load_video_stream(self, video, index):
        if video.info is not None:
            # first we split the mapping on the commas
            stream_map = _get_stream_map(video.info)
            # Just collect the stream we want
            string = stream_map[int(index)]
            video.stream = self._get_stream(video, string, int(index))


# Taken from from Pafy https://github.com/np1/pafy
ITAGS = {
    '5': ('320x240', 'flv', "normal", ''),
    '17': ('176x144', '3gp', "normal", ''),
    '18': ('640x360', 'mp4', "normal", ''),
    '22': ('1280x720', 'mp4', "normal", ''),
    '34': ('640x360', 'flv', "normal", ''),
    '35': ('854x480', 'flv', "normal", ''),
    '36': ('320x240', '3gp', "normal", ''),
    '37': ('1920x1080', 'mp4', "normal", ''),
    '38': ('4096x3072', 'mp4', "normal", '4:3 hi-res'),
    '43': ('640x360', 'webm', "normal", ''),
    '44': ('854x480', 'webm', "normal", ''),
    '45': ('1280x720', 'webm', "normal", ''),
    '46': ('1920x1080', 'webm', "normal", ''),
    # '59': ('1x1', 'mp4', 'normal', ''),
    # '78': ('1x1', 'mp4', 'normal', ''),
    '82': ('640x360-3D', 'mp4', "normal", ''),
    '83': ('640x480-3D', 'mp4', 'normal', ''),
    '84': ('1280x720-3D', 'mp4', "normal", ''),
    '100': ('640x360-3D', 'webm', "normal", ''),
    '102': ('1280x720-3D', 'webm', "normal", ''),
    '133': ('426x240', 'm4v', 'video', ''),
    '134': ('640x360', 'm4v', 'video', ''),
    '135': ('854x480', 'm4v', 'video', ''),
    '136': ('1280x720', 'm4v', 'video', ''),
    '137': ('1920x1080', 'm4v', 'video', ''),
    '138': ('4096x3072', 'm4v', 'video', ''),
    '139': ('48k', 'm4a', 'audio', ''),
    '140': ('128k', 'm4a', 'audio', ''),
    '141': ('256k', 'm4a', 'audio', ''),
    '160': ('256x144', 'm4v', 'video', ''),
    '167': ('640x480', 'webm', 'video', ''),
    '168': ('854x480', 'webm', 'video', ''),
    '169': ('1280x720', 'webm', 'video', ''),
    '170': ('1920x1080', 'webm', 'video', ''),
    '171': ('128k', 'ogg', 'audio', ''),
    '172': ('192k', 'ogg', 'audio', ''),
    '218': ('854x480', 'webm', 'video', 'VP8'),
    '219': ('854x480', 'webm', 'video', 'VP8'),
    '242': ('360x240', 'webm', 'video', 'VP9'),
    '243': ('480x360', 'webm', 'video', 'VP9'),
    '244': ('640x480', 'webm', 'video', 'VP9'),
    '245': ('640x480', 'webm', 'video', 'VP9'),
    '246': ('640x480', 'webm', 'video', 'VP9'),
    '247': ('720x480', 'webm', 'video', 'VP9'),
    '248': ('1920x1080', 'webm', 'video', 'VP9'),
    '256': ('192k', 'm4a', 'audio', '6-channel'),
    '258': ('320k', 'm4a', 'audio', '6-channel'),
    '264': ('2560x1440', 'm4v', 'video', ''),
    '271': ('1920x1280', 'webm', 'video', 'VP9'),
    '272': ('3414x1080', 'webm', 'video', 'VP9')
}


def _get_itags(itag):
    return [t for t in ITAGS.get(itag, ()) if t]


def _get_resolution(itag):
    return ITAGS.get(itag, ('', ''))[0]


def _get_extension(itag):
    return ITAGS.get(itag, ('', ''))[1]


def _get_stream_map(info):
    return (tf(info.get('url_encoded_fmt_stream_map', '')).split(',') +
            tf(info.get('adaptive_fmts', '')).split(','))
