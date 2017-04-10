import urllib


def take_first(values):
    if isinstance(values, str):
        return values

    if values is not None:
        for value in values:
            if value is not None and value != '':
                return value


def get_video_id(video):
    if '/watch' in video:
        parts = urllib.parse.urlsplit(video)
        info = urllib.parse.parse_qs(parts.query)
        vid = take_first(info.get('v'))
        return vid

    return video
