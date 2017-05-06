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
        if info is not None:
            # first we split the mapping on the commas
            stream_map = clipy.youtube.get_stream_map(self.info)

            # Check it we only want a specific stream
            if index is None:
                # collect all streams data since we don't have a stream index
                for i, string in enumerate(stream_map):
                    stream = self._get_stream(string, i)
                    self.streams.append(stream)
            else:
                # Just collect the stream we want
                string = stream_map[int(index)]
                self.stream = self._get_stream(string, int(index))

    def _get_stream(self, string, index):
        data = {k: tf(v) for k, v in urllib.parse.parse_qs(string).items()}
        itag = data.get('itag', None)
        data.update(
            resolution=clipy.youtube.get_resolution(itag),
            extension=clipy.youtube.get_extension(itag),
            title=self.info.get('title', '<NOTITLE>'),
        )
        return StreamModel(data, self, index)

    def __getattr__(self, field_name):
        """
        Check if our attribute exists for the object, otherwise return the
        corresponding entry from our 'info'.
        """
        # from pprint import pformat
        # # import pdb; pdb.set_trace()
        # sdict = pformat(self.__dict__)
        # dname = self.__dict__.get(field_name, '?.')
        # mname = self.info_map.get(field_name, field_name)
        # ninfo = self.info.get(mname)
        # finfo = tf(ninfo)
        # with open('getattr.{}'.format(field_name), 'w') as f:
        #     f.write('field_name:  '); f.write(     field_name ); f.write('\n\n')
        #     f.write('dict:  '); f.write(    sdict ); f.write('\n\n')
        #     f.write('dname: '); f.write(    dname ); f.write('\n\n')
        #     f.write('mname: '); f.write(    mname ); f.write('\n\n')
        #     f.write('ninfo: '); f.write(str(ninfo)); f.write('\n\n')
        #     f.write('finfo: '); f.write(    finfo ); f.write('\n\n')
        return self.__dict__.get(
            field_name,
            tf(
                self.info.get(
                    self.info_map.get(field_name, field_name))))

    def __str__(self):
        return 'V> {duration}  {title}  {path}'.format(
            duration=self.duration, title=self.title, path=self.path)

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
        return 'S> {} {}'.format(self.status, self.display)

    @property
    def serial(self):
        return dict(**self.__dict__, **dict(status=self.status, display=self.display))

    @property
    def status(self):
        bytesdone = int(self.progress.get('bytesdone', 0))
        elapsed = int(self.progress.get('elapsed', 0))
        offset = int(self.progress.get('offset', 0))
        total = int(self.progress.get('total', 0))

        if not (total and elapsed):
            return 'Huh?'

        rate = ((bytesdone - offset) / 1024) / elapsed
        eta = (total - bytesdone) / (rate * 1024)

        return '{m}| {d:,} ({p:.0%}) {t} @ {r:.0f} KB/s {e:.0f} s'.format(
            m=clipy.utils.progress_bar(bytesdone, total),
            d=bytesdone,
            t=clipy.utils.size(total),
            p=bytesdone * 1.0 / total,
            r=rate,
            e=eta,
        )

    @property
    def display(self):
        return '{}; {} {}'.format(', '.join(self.itags),
                                  getattr(self, 'quality', ''),
                                  getattr(self, 'type', ''))

    def detail(self):
        return '\n'.join(clipy.utils.list_properties(self))
