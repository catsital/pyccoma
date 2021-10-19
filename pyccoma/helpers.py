import os
import re
import logging

log = logging.getLogger(__name__)

def safe_filename(title: str) -> str:
    pattern = re.compile(r'[?"|:<>*/\\]', flags=re.VERBOSE)
    return pattern.sub("", str(title))

def create_path(path: str) -> str:
    if path:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

    if os.path.exists(path):
        log.warning('Path already exists: {0}'.format(path))
    else:
        log.debug('Creating path: {0}'.format(path))

    os.makedirs(path, exist_ok=True)
    return path

def create_tags(text: str) -> str:
    identifiers = [
        r'is_limited_read',
        r"is_limited_free",
        r"is_already_read",
        r"is_free",
        r"is_purchased",
    ]
    identifiers = "|".join(identifiers)
    pattern = r'(\b' + identifiers + r')\b(\s*(' + identifiers + r')\b)*'

    regex = re.compile(pattern, re.I)
    tags = regex.sub(r"episode['\1']", text.strip('"'))
    return tags

def trunc_title(title: str) -> str:
    return re.sub(r'\((?:[^)(]|\([^)(]*\))*\)', '', title)

def valid_url(url: str) -> bool:
    base_url = r'(http|https)://(|www.)piccoma.com/web'
    urls = [
        base_url + r'/product/([0-9\-]+)/episodes\?etype\=([eE|vV]+)',
        base_url + r'/viewer/(|s/)([0-9]+)/([0-9]+)',
        base_url + r'/bookshelf/|(bookmark|history|purchase)'
    ]
    urls = "|".join(urls)
    regex = re.search(urls, url)
    return bool(regex)

def is_episode_url(url: str) -> bool:
    return True if 'viewer' in url else False
