#!/usr/bin/env python3
import re
import tempfile
import os
import sys
import shutil
import random
import string
import logging
from multiprocessing.dummy import Pool
from distutils.spawn import find_executable
import subprocess
import argparse
from datetime import datetime

import requests


RETRY_LIMIT = 3
DOWNLOAD_THREADS = 4
WORKING_DIR = os.path.join(
    tempfile.gettempdir(),
    'triplej_dl',
    ''.join(random.choice(string.ascii_letters) for _ in range(8)),
)
OUTPUT_TS_PATH = os.path.join(WORKING_DIR, 'concat.ts')
CONCAT_LIST_PATH = os.path.join(WORKING_DIR, 'concat.txt')
CDN_BASE_URL = 'http://abcradiomodhls.abc-cdn.net.au/i/triplej/audio'

try:
    import tenacity

    @tenacity.retry(
        wait=tenacity.wait_random_exponential(multiplier=1, max=10),
        stop=tenacity.stop_after_attempt(RETRY_LIMIT)
    )
    def _download(url):
        r = requests.get(url)
        if r.status_code != 404:  # no point to retry on 404 errors
            r.raise_for_status()
        return r

except ImportError:
    print('Tenacity Python package not found, retries on download errors disabled')

    def _download(url):
        r = requests.get(url)
        if r.status_code != 404:  # no point to retry on 404 errors
            r.raise_for_status()
        return r


def get_download_urls(page_url: str):
    r = requests.get(page_url)
    r.raise_for_status()
    master_playlist_url = re.search('.*(http.*master.m3u8).*', r.text).groups()[0]

    r = requests.get(master_playlist_url)
    r.raise_for_status()
    playlist_url = re.search('.*(http://.*m3u8).*', r.text).groups()[0]

    r = requests.get(playlist_url)
    r.raise_for_status()
    return re.findall('.*(http://.*.ts).*', r.text)


def download_file(url, output_dir: str=WORKING_DIR):
    logger.info('Downloading {}'.format(url))
    output_path = os.path.join(output_dir, url.split('/')[-1])
    try:
        r = _download(url)
    except:
        logger.error('Exceeded retries trying to download {}'.format(url))
        return None
    if r.status_code == 404:
        logger.error('{} returned 404; continuing without this file'.format(url))
        return None
    with open(output_path, 'wb') as f:
        f.write(r.content)
    return 'success'


def main(url: str, output_dir: str, show_str: str, show_date: str, show_minutes: int):
    ffmpeg = find_executable('ffmpeg')
    if not ffmpeg:
        raise Exception('ffmpeg not found in PATH, please install ffmpeg and retry')

    os.makedirs(WORKING_DIR)
    logger.info('Temporary working directory is: {}'.format(WORKING_DIR))

    if url:
        download_urls = get_download_urls(url)
    else:
        try:
            datetime.strptime(show_date, '%Y-%m-%d')
        except ValueError:
            logger.error('Date format incorrect, must be YYYY-MM-DD')
            exit(1)
        show_segments = show_minutes * 6 + 1  # 10 second segments
        download_urls = [
            os.path.join(CDN_BASE_URL, f'{show_str.lower()}-{show_date}.m4a', f'segment{i}_0_a.ts')
            for i in range(1, show_segments + 1)
        ]

    pool = Pool(DOWNLOAD_THREADS)
    download_status = pool.map(download_file, download_urls)
    pool.close()
    pool.join()

    fns = [i.split('/')[-1] for i in download_urls]
    fns_downloaded = [fn for fn, status in zip(fns, download_status) if status]
    with open(CONCAT_LIST_PATH, 'w') as f:
        f.write('file ' + '\nfile '.join(fns_downloaded))

    logger.info('Concatenating files')  # join into a single file containing aac data
    subprocess.run(
        [ffmpeg, '-safe', '0', '-f', 'concat', '-i', CONCAT_LIST_PATH, '-acodec', 'copy', OUTPUT_TS_PATH],
        check=True, stdout=subprocess.PIPE
    )

    logger.info('Writing output file')  # put in m4a container to enable proper timestamp-based seeking
    output_filename = download_urls[0].split('/')[-2]
    subprocess.run(
        [ffmpeg, '-err_detect', 'ignore_err', '-i', OUTPUT_TS_PATH, '-c', 'copy', os.path.join(output_dir, output_filename)],
        check=True, stdout=subprocess.PIPE
    )

    logger.info('Completed successfully')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=__file__)
    parser.add_argument(
        'url', type=str, help='The page URL containing the program to download', nargs='?')
    parser.add_argument(
        'output_dir', type=str, default=os.path.join(os.path.expanduser('~'), 'Downloads'), nargs='?',
        help='Where the output file will be written to, by default ~/Downloads')
    parser.add_argument(
        '-s', '--show_str', type=str, nargs='?',
        help='Instead of providing `url`, you can instead pass the show stream string (e.g. fns for Friday Night Shuffle) '
             'along with the show date and show number, and the CDN download URLs will be constructed from these')
    parser.add_argument(
        '-d', '--show_date', type=str, nargs='?',
        help='Only needed if not passing `url`, A string representing the date of the show, e.g. 2018-05-18 for May 18th.')
    parser.add_argument(
        '-mins', '--show_minutes', type=int, default=180, nargs='?',
        help='Only needed if not passing `url`, number of minutes in the show')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = vars(parser.parse_args())

    if not args['url']:
        assert all([i is not None for i in (args['show_str'], args['show_date'])]), 'If `url` is not provided, both ' \
                                                                                    '`show_str` and `show_date` are required.'

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    try:
        main(**args)
    except:
        raise
    finally:
        shutil.rmtree(WORKING_DIR)
