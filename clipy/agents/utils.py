import urllib.parse

from .youtube import YoutubeAgent
from .vidme import VidmeAgent


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

    raise Exception(f'No suitable video agent found for: {vid}')
