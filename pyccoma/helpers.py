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
