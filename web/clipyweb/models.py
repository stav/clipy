import os
import urllib

import clipyweb.youtube

from clipyweb.utils import take_first as tf


class VideoDetail(object):
    """ Video information container """
    info = dict()
    stream = None
    streams = list()
    info_map = dict(
        videoid='video_id',
        duration='length_seconds',
    )

    def __init__(self, data=None, target=None):
        if data is not None:
            # data is url querystring format, so we need to parse it
            self.info = urllib.parse.parse_qs(data)

            # first we split the mapping on the commas
            stream_map = clipyweb.youtube.get_stream_map(self.info)

            # then we zip/map the values into our streams list
            streams = [{k: tf(v)
                        for k, v in sdic.items()}
                       for sdic in [urllib.parse.parse_qs(mapp)
                                    for mapp in stream_map]]

            # now add in our new fields
            self.streams = []
            for stream in streams:

                itag = stream.get('itag', None)

                stream.update(
                    resolution=clipyweb.youtube.get_resolution(itag),
                    extension=clipyweb.youtube.get_extension(itag),
                    title=self.info.get('title', '<NOTITLE>'),
                )
                self.streams.append(Stream(stream, video=self, target=target))

                # from pprint import pformat
                # # info = pformat(self.info)
                # # strm = pformat(self.streams)
                # strm = pformat([str(s) for s in self.streams])
                # with open('INIT', 'a') as f:
                #     # f.write('data: '); f.write(data); f.write('\n\n')
                #     # f.write('info: '); f.write(info); f.write('\n\n')
                #     # f.write('stream_map: '); f.write(str(stream_map)); f.write('\n\n')
                #     f.write('strm: '); f.write(strm); f.write('\n\n')
                #     f.write('------------------------------------\n\n')

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


class Stream(object):
    """ Video stream """
    itags = []
    itag = None
    name = None
    path = None
    status = ''

    def __init__(self, info, video=None, target=None):
        """  """
        # First load all info items into the object namespace
        for k, v in info.items():
            setattr(self, k, tf(v))

        # Declare the stream/file name using the title et.al.
        self.name = video.name or '{}-({}).{}'.format(
            video.title, info.get('resolution', ''), info.get('extension', '')
        ).replace('/', '|')

        # Declare the path using the name
        self.path = os.path.join(target or '.', self.name)

        # Declare the tags
        self.itags = clipyweb.youtube.get_itags(info.get('itag', None))

    def __str__(self):
        # from pprint import pformat
        # x = pformat(self.type)
        # with open('Stream.__str__', 'a') as f:
        #     f.write('x: '); f.write(x); f.write('\n\n')
        #     f.write('------------------------------------\n\n')
        return 'S> {} {}'.format(self.status, self.display)

    @property
    def display(self):
        return 'Sd> {}; {} {}'.format(', '.join(self.itags),
                                      getattr(self, 'quality', ''),
                                      getattr(self, 'type', ''))

    def detail(self):
        return '\n'.join(clipyweb.utils.list_properties(self))
