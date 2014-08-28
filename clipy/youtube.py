"""
Clipy YouTube video downloader YouTube module
"""
import asyncio
import urllib

import clipy.request
import clipy.video
import clipy.utils

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


@asyncio.coroutine
def get_info(resource):
    url = 'https://www.youtube.com/get_video_info?video_id={}'.format(resource)
    try:
        data = yield from clipy.request.get_text(url)

    except ConnectionError as ex:
        raise ConnectionError from ex

    info = urllib.parse.parse_qs(data)

    status = clipy.utils.take_first(info.get('status', None))
    if status == 'ok':
        return data
    else:
        raise ConnectionError('Invalid video Id "{}" {}'.format(resource, info))


@asyncio.coroutine
def get_video(resource, target=None):
    # try:
    #     data = yield from clipy.request.get_youtube_info(resource)
    # except ConnectionError as ex:
    #     self.console.printstr(ex, error=True)
    #     return
    # if data is None:
    #     self.console.printstr('No data returned', error=True)
    #     return

    # Pull out just the 11-digit Id from the URL
    if 'youtube.com/watch?v=' in resource:
        pos = resource.find('/watch?v=') + 9
        resource = resource[pos: pos+11]

    try:
        data = yield from get_info(resource)

    except ConnectionError as ex:
        raise ConnectionError from ex

    return clipy.video.VideoDetail(data, target=target)
