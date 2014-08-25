"""
Clipy YouTube video downloader video module
"""
import urllib

import clipy.utils


class VideoDetail(object):
    info = dict()
    stream = None
    streams = list()
    info_map = dict(
        videoid='video_id',
        duration='length_seconds',
    )

    def __init__(self, data=None):
        if data is not None:
            # data is url querystring format, so we need to parse it
            self.info = urllib.parse.parse_qs(data)

            # first we split the mapping on the commas
            stream_map = clipy.utils.take_first(
                self.info.get('url_encoded_fmt_stream_map', ())).split(',')

            # then we zip/map the values into our streams list
            streams = [{k: clipy.utils.take_first(v)
                       for k, v in sdic.items()}
                       for sdic in [urllib.parse.parse_qs(mapp)
                       for mapp in stream_map]]

            # now add in our new fields
            self.streams = []
            for stream in streams:

                itags = [t for t in clipy.youtube.ITAGS.get(
                    stream.get('itag', None)) if t]

                stream.update(dict(
                    resolution=itags[0]),
                    extension=itags[1],
                    title=self.info.get('title', '<NOTITLE>'),
                )
                self.streams.append(Stream(stream))

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

    def __getattr__(self, name):
        """
        Check if our attribute exists for the object, otherwise return the
        corresponding entry from our 'info'.
        """
        # from pprint import pformat
        # print('!!!!!!!!!', name)
        # # import pdb; pdb.set_trace()
        # sdict = pformat(self.__dict__)
        # dname = self.__dict__.get(name, '?.')
        # mname = self.info_map.get(name, name)
        # ninfo = self.info.get(mname)
        # finfo = clipy.utils.take_first(ninfo)
        # with open('getattr.{}'.format(name), 'w') as f:
        #     f.write('name:  '); f.write(     name ); f.write('\n\n')
        #     f.write('dict:  '); f.write(    sdict ); f.write('\n\n')
        #     f.write('dname: '); f.write(    dname ); f.write('\n\n')
        #     f.write('mname: '); f.write(    mname ); f.write('\n\n')
        #     f.write('ninfo: '); f.write(str(ninfo)); f.write('\n\n')
        #     f.write('finfo: '); f.write(    finfo ); f.write('\n\n')
        return self.__dict__.get(
            name,
            clipy.utils.take_first(
                self.info.get(
                    self.info_map.get(name, name))))

    def __str__(self):
        return 'V> {duration}  {title}  {path}'.format(
            duration=self.duration, title=self.title, path=self.path)

    @property
    def detail(self):
        # import pprint
        # p = pprint.pformat(self.info)
        return '''
Id:     {}
Title:  {}
Author: {}
Length: {} seconds
Views:  {}

Streams: {}
* {}
        '''.format(
            clipy.utils.take_first(self.info['video_id']),
            clipy.utils.take_first(self.info['title']),
            clipy.utils.take_first(self.info['author']),
            clipy.utils.take_first(self.info['length_seconds']),
            clipy.utils.take_first(self.info['view_count']),
            len(self.streams),
            '\n* '.join([stream.display for stream in self.streams]),
        )
        # with open('qs', 'w') as f:
        #     f.write(output)


class Stream(object):
    """Video stream """
    name = None
    path = None
    itags = []
    stream = None
    status = ''

    def __init__(self, stream):
        self.stream = stream
        self.itags = [t for t in clipy.youtube.ITAGS.get(
            stream.get('itag', None)) if t]

    def __getattr__(self, name):
        """
        Check if our attribute exists for the object, otherwise return the
        corresponding entry from our 'stream'.
        """
        return self.__dict__.get(name, self.stream.get(name))

    def __str__(self):
        # from pprint import pformat
        # # info = pformat(self.info)
        # strm = pformat(self.stream)
        # with open('Stream.__str__', 'a') as f:
        #     # f.write('data: '); f.write(data); f.write('\n\n')
        #     # f.write('info: '); f.write(info); f.write('\n\n')
        #     # f.write('stream_map: '); f.write(str(stream_map)); f.write('\n\n')
        #     f.write('strm: '); f.write(strm); f.write('\n\n')
        #     f.write('------------------------------------\n\n')

        return 'S> {} {}'.format(self.status, self.display or self.name or self.title)

    @property
    def display(self):
        return '{} ({}) {}'.format(', '.join(self.itags),
                                   self.stream.get('quality', 'unknown'),
                                   self.stream.get('type', ''))
