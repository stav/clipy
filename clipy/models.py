import urllib
import logging

import clipy.youtube
import clipy.utils

from clipy.utils import take_first as tf

logger = logging.getLogger(__name__)


class VideoModel():
    """Video information container

    stream_map:

        ['init=0-4451&projection_type=1&bitrate=72530&fps=1&url=https%3A%2F%2Fr3---sn-j5caxh5n...']

    streams:

         [{'bitrate': '72530',
           'clen': '73646',
           'fps': '1',
           'index': '4452-4470',
           'init': '0-4451',
           'itag': '171',
           'lmt': '1392038165904022',
           'projection_type': '1',
           'type': 'audio/webm; codecs="vorbis"',
           'url': 'https://r3---sn-j5caxh5n-upwl.googlevideo.com/videoplayback?mv=m&mt=14...'},...]
    """
    def __init__(self, vid: str, info: dict = None, index: int = None) -> None:
        self.vid = vid
        self.info = info
        self.stream = None
        self.streams = list()
        self.info_map = dict(
            videoid='video_id',
            duration='length_seconds',
        )

        def get_stream(string, index):
            data = {k: tf(v) for k, v in urllib.parse.parse_qs(string).items()}
            itag = data.get('itag', None)
            data.update(
                resolution=clipy.youtube.get_resolution(itag),
                extension=clipy.youtube.get_extension(itag),
                title=self.info.get('title', '<NOTITLE>'),
            )
            return StreamModel(data, self, index)

        if info is not None:
            # first we split the mapping on the commas
            stream_map = clipy.youtube.get_stream_map(self.info)

            # Check it we only want a specific stream
            if index is None:
                # collect all streams data since we don't have a stream index
                for i, string in enumerate(stream_map):
                    stream = get_stream(string, i)
                    self.streams.append(stream)
            else:
                # Just collect the stream we want
                string = stream_map[int(index)]
                self.stream = get_stream(string, int(index))

    def __getattr__(self, field_name):
        """Check if our attribute exists for the object, otherwise return the corresponding entry
        from our 'info'.
        """
        return self.__dict__.get(
            field_name,
            tf(
                self.info.get(
                    self.info_map.get(field_name, field_name))))

    def __str__(self):
        return '<{cls}> {duration} {title}'.format(
            cls=self.__class__.__name__, duration=self.duration, title=self.title)

    @property
    def detail(self):
        streams = ''

        for i, stream in enumerate(self.streams):
            if hasattr(stream, 'url'):
                streams += '{}: {}\n'.format(i, stream.display)

        return '''
Id:     {}
Title:  {}
Author: {}
Length: {} seconds
Views:  {}

Streams: {}
{}'''.format(
            tf(self.info['video_id']),
            tf(self.info['title']),
            tf(self.info['author']),
            tf(self.info['length_seconds']),
            tf(self.info['view_count']),
            len(self.streams),
            streams,
        )
        # with open('qs', 'w') as f:
        #     f.write(output)


class StreamModel():
    """ Video stream """
    def __init__(self, info, video, index):
        """  """
        # Initialize some main properties
        self.itags = []
        self.index = index
        self.itag = None
        self.name = None
        self.sid = f'{video.vid}|{index}'
        self.url = None
        self.progress = dict()

        # Load all info items into the object namespace
        for k, v in info.items():
            setattr(self, k, tf(v))

        # Declare the stream/file name using the title et.al.
        self.name = video.name or '{}-({}){}.{}'.format(
            video.title,
            info.get('resolution', ''),
            video.vid,
            info.get('extension', ''),
        ).replace('/', '|')

        # Declare the tags
        self.itags = clipy.youtube.get_itags(info.get('itag', None))

        logger.debug(f'Stream {index} {self.name}')

    def __str__(self):
        return f'{self.display} {self.status}'

    @property
    def serial(self):
        return dict(**self.__dict__, **dict(status=self.status, display=self.display))

    @property
    def status(self):
        bytesdone = int(self.progress.get('bytesdone', 0))
        total = int(self.progress.get('total', 0))

        return '{d:,} ({p:.0%}) {t} @ {r:.0f} KB/s {e:.0f} s'.format(
            d=bytesdone,
            t=clipy.utils.size(total),
            p=(bytesdone * 1.0 / total) if total else 0.0,
            r=self.rate,
            e=self.eta,
        )

    @property
    def rate(self):
        bytesdone = int(self.progress.get('bytesdone', 0))
        elapsed = int(self.progress.get('elapsed', 0))
        offset = int(self.progress.get('offset', 0))

        return (((bytesdone - offset) / 1024) / elapsed) if elapsed else 0.0

    @property
    def eta(self):
        bytesdone = int(self.progress.get('bytesdone', 0))
        total = int(self.progress.get('total', 0))
        rate = self.rate

        return (total - bytesdone) / (rate * 1024) if rate else 0.0

    @property
    def display(self):
        return '{}; {} {}'.format(', '.join(self.itags),
                                  getattr(self, 'quality', ''),
                                  getattr(self, 'type', ''))

    @property
    def detail(self):
        return '\n'.join(clipy.utils.list_properties(self))
