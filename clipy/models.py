import string
import logging

import clipy.utils

from clipy.utils import take_first as tf

logger = logging.getLogger(__name__)


class Model():
    """Base model
    """
    def __repr__(self):
        return '\n\n'.join(clipy.utils.list_properties(self))

    def detail(self):
        return clipy.utils.dict_properties(self)


class VideoModel(Model):
    """Video information container
    """
    def __init__(self, vid, info) -> None:
        self.vid = vid
        self.info = info
        self.stream = None
        self.streams = list()
        self.info_map = dict()

    def __getattr__(self, field_name):
        """Check if our attribute exists for the object, otherwise return the corresponding entry
        from our 'info'.
        """
        return self.__dict__.get(
            field_name,
            self.info.get(
                self.info_map.get(field_name, field_name)))

    def __str__(self):
        return '<{cls}> {duration} {title}'.format(
            cls=self.__class__.__name__, duration=self.duration, title=self.title)


class StreamModel(Model):
    """Video stream
    """
    def __init__(self, info, video, index):
        """  """
        # Initialize some main properties
        self.progress = dict()
        self.display = str(index)
        self.index = index
        self.name = StreamModel.safe_name(video.name or video.title)
        self.type = None
        self.sid = f'{video.vid}|{index}'
        self.vid = video.vid
        self.url = None

        # Load all info items into the object namespace
        for k, v in info.items():
            setattr(self, k, tf(v))

        logger.debug(f'Stream {index} {self.name}')

    def __str__(self):
        return f'display: {self.display}, status: {self.status}'

    @property
    def serial(self):
        data = dict(self.__dict__)
        data.update(status=self.status)
        return data

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

    @staticmethod
    def safe_name(name: str):
        white_chars = string.ascii_letters + string.digits + '!|()-.,_'
        return ''.join(s for s in name if s in white_chars).strip()
