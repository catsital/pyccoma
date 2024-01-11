#!/usr/bin/env python

import argparse

import os
import re
import logging
from getpass import getpass
from typing import Optional, Tuple, List
from itertools import chain

from pyccoma.jp.pyccoma import Pyccoma as Jp
from pyccoma.fr.pyccoma import Pyccoma as Fr
from pyccoma.exceptions import PyccomaError
from pyccoma.logger import setup_logging, levels
from pyccoma.helpers import create_tags

log = logging.getLogger(__name__)


def main() -> None:
    try:
        global pyccoma, region

        setup_logging()
        parser = construct_parser()
        args = parser.parse_args()

        region = args.region.lower()

        if region == 'jp':
            pyccoma = Jp()
        elif region == 'fr':
            pyccoma = Fr()
        else:
            raise ValueError("Invalid region specified.")

        url = args.url
        pyccoma.format = args.format
        pyccoma.manga = args.etype[0]
        pyccoma.smartoon = args.etype[1]
        pyccoma.novel = args.etype[2]
        pyccoma.zeropad = args.pad
        pyccoma.retry_count = args.retry_count
        pyccoma.retry_interval = args.retry_interval
        pyccoma.archive = args.archive
        pyccoma.omit_author = args.omit_author

        logging.getLogger().setLevel(args.loglevel)

        if not (
            args.range and 'viewer' not in args.url
        ) and (
            args.filter == 'custom'
        ):
            raise PyccomaError("Use --filter custom along with --range.")

        elif (
            args.range and not args.filter
        ) or (
            args.range and args.filter in ('min', 'max', 'all')
        ):
            log.warning(f"Overriding --filter={args.filter} to parse custom.")
            args.filter = 'custom'

        password = ""

        if args.email:
            if not password:
                password = getpass()

            pyccoma.login(args.email, password)

        if args.url and args.filter:
            if args.url[0] in ('history', 'bookmark', 'purchase'):
                if args.url[0] in 'history':
                    url = pyccoma.get_history().values()
                    log.info(
                        f"Parsing ({len(url)}) titles from your history."
                    )

                elif args.url[0] in 'bookmark':
                    url = pyccoma.get_bookmark().values()
                    log.info(
                        f"Parsing ({len(url)}) titles from your bookmarks."
                    )

                elif args.url[0] in 'purchase':
                    url = pyccoma.get_purchase().values()
                    log.info(
                        f"Parsing ({len(url)}) titles from your purchases."
                    )

            elif valid_url(args.url[0], level=3):
                raise PyccomaError(
                    "There is nothing to aggregate. You should only use "
                    "--filter on a product page or your library."
                )

        if any(map(valid_url, args.url)):
            if not os.path.exists(args.output) and not args.output:
                log.warning(
                    "No path found, creating an extract folder inside "
                    "the current working directory: {0}".format(os.getcwd())
                )
            fetch(
                url,
                args.filter,
                args.range,
                args.include,
                args.exclude,
                args.output
            )
        else:
            raise ValueError("Invalid url.")

    except Exception as error:
        parser.error(error)


def construct_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyccoma",
        description="Scrape and download from Piccoma.",
        epilog="""
        Report bugs and make feature requests at
        https://github.com/catsital/pyccoma/issues
        """,
        add_help=False,
    )

    required = parser.add_argument_group("Required options")
    required.add_argument(
        "url",
        nargs="*",
        help="""
        Link to an episode or product. If logged in, use: history, bookmark,
        or purchase as shorthand to your library.
        """
    )

    optional = parser.add_argument_group("General options")
    optional.add_argument(
        "-o",
        "--output",
        type=str,
        default="extract",
        help="Path to save downloaded images."
    )
    optional.add_argument(
        "-f",
        "--format",
        type=str,
        default="png",
        help="Image format: png, jpeg, jpg, gif, bmp (Default: png)"
    )
    optional.add_argument(
        "-p",
        "--pad",
        type=int,
        metavar=("LENGTH"),
        default=0,
        help="Pad page numbers with leading zeroes (Default: 0)"
    )
    optional.add_argument(
        "--archive",
        dest="archive",
        action="store_true",
        default=False,
        help="Output to cbz archive format."
    )
    optional.add_argument(
        "--omit-author",
        dest="omit_author",
        action="store_true",
        default=False,
        help="Omit author(s) in title naming scheme."
    )

    locale = parser.add_argument_group("Locale options")
    locale.add_argument(
        "--region",
        type=str,
        default="Jp",
        help="Select which Piccoma service to use. (Default: Jp)"
    )

    retry = parser.add_argument_group("Retry options")
    retry.add_argument(
        "--retry-count",
        type=int,
        metavar=("COUNT"),
        default=3,
        help="Number of download retry attempts. (Default: 3)"
    )
    retry.add_argument(
        "--retry-interval",
        type=int,
        metavar=("SECONDS"),
        default=1,
        help="Delay between each retry attempt. (Default: 1)"
    )

    user = parser.add_argument_group("Login options")
    user.add_argument(
        "--email",
        type=str,
        help="Account email address."
    )

    filter = parser.add_argument_group("Filter options")
    filter.add_argument(
        "--etype",
        type=str,
        nargs=3,
        metavar=("MANGA", "SMARTOON", "NOVEL"),
        default=["volume", "episode", "episode"],
        help="""
        Preferred episode type to scrape manga, smartoon and novel when
        aggregating your library. (Default: manga=volume
        smartoon=episode novel=episode)
        """
    )
    filter.add_argument(
        "--filter",
        type=str,
        help="""
        Filter to use when aggregating products or scraping library. Can be
        either: min, max, all, or custom with --range.
        """
    )
    filter.add_argument(
        "--range",
        type=int,
        nargs=2,
        metavar=("START", "END"),
        help="Range to use when scraping episodes or volumes."
    )
    filter.add_argument(
        "--include",
        type=include,
        default="episode",
        help="""
        Arguments to include when parsing your library: is_purchased, is_free,
        is_zero_plus, is_already_read, is_read_for_free, is_wait_until_free
        """
    )
    filter.add_argument(
        "--exclude",
        type=exclude,
        default="",
        help="""
        Arguments to exclude when parsing your library: is_purchased, is_free,
        is_zero_plus, is_already_read, is_read_for_free, is_wait_until_free
        """
    )

    logger = parser.add_argument_group("Logging options")
    logger.add_argument(
        "-l", "--loglevel",
        metavar="LEVEL",
        choices=levels,
        default="info",
        help="""
        Set the log message threshold. Valid levels are: debug, info, warning,
        error, none (Default: info)
        """
    )

    info = parser.add_argument_group("Info")
    info.add_argument(
        "-h", "--help",
        action="help",
        help="Show this help message and exit."
    ),
    info.add_argument(
        "-v", "--version",
        action="version",
        help="Show program version.",
        version="%(prog)s 0.6.1"
    )

    return parser


def include(value: str) -> str:
    try:
        include = create_tags(value).replace("&", " and ").replace("|", " or ")
        return include
    except Exception:
        raise argparse.ArgumentTypeError(
            'Specify type in this format: "is_free|is_already_read"'
        )


def exclude(value: str) -> str:
    try:
        exclude = create_tags(value).replace("&", " and ").replace("|", " or ")
        return exclude
    except Exception:
        raise argparse.ArgumentTypeError(
            'Specify type in this format: "is_free&is_already_read"'
        )


def valid_url(url: str, level: Optional[int] = None) -> bool:
    if region == 'jp':
        base_url = r"(http|https)://(|www.)(|jp.)piccoma.com/web"
        urls = [
            base_url + r"/product/([0-9\-]+)/episodes\?etype\=([eE|vV]+)",
            base_url + r"/product/([0-9\-]+)/episodes\?etype\=([eE]+)",
            base_url + r"/product/([0-9\-]+)/episodes\?etype\=([vV]+)",
            base_url + r"/viewer/(|s/)([0-9]+)/([0-9]+)",
            base_url + r"/bookshelf/|(bookmark|history|purchase)"
        ]
    elif region == 'fr':
        base_url = r"(http|https)://(|www.)(|fr.)piccoma.com/fr"
        urls = [
            base_url + r"/product/([episode|volume]+)/([0-9\-]+)",
            base_url + r"/product/episode/([0-9\-]+)",
            base_url + r"/product/volume/([0-9\-]+)",
            base_url + r"/viewer/([0-9]+)/([0-9]+)",
            base_url + r"/bookshelf/|(bookmark|history|purchase)"
        ]
    else:
        raise ValueError("Invalid input.")

    if not level:
        urls = "|".join(urls)
        regex = re.search(urls, url)
    else:
        regex = re.search(urls[level], url)
    return bool(regex)


def fetch(
    url: List[str],
    mode: Optional[str] = None,
    range: Optional[Tuple[int, int]] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    output: Optional[str] = None
) -> None:
    if mode:
        try:
            if not range:
                range = (0, 0)

            if exclude:
                exclude = f" {'and ' if include else ''}not ({exclude})"

            product = []

            for title in url:
                product.append([
                    episode['url']
                    for episode in pyccoma.get_list(title).values()
                    if eval((include) + (exclude))
                ])

            if 'min' in mode:
                product = [episode[0] for episode in product if episode]
            elif 'max' in mode:
                product = [episode[-1] for episode in product if episode]
            elif 'all' in mode:
                product = list(chain.from_iterable(product))
            elif 'custom' in mode:
                product = list(chain.from_iterable(product))[range[0]:range[1]]
            else:
                raise ValueError

            log.info("Fetching ({0}) items.".format(total := len(product)))

            for index, item in enumerate(product):
                log.info(f"Fetching ({index+1}/{total})")
                pyccoma.fetch(item, output)

        except Exception as error:
            raise PyccomaError(error)

    else:
        for index, link in enumerate(url):
            if valid_url(url=link, level=3):
                log.info(f"Fetching ({index+1}/{len(url)})")
                pyccoma.fetch(link, output)
            elif valid_url(url=link, level=0):
                raise PyccomaError(
                    "Use --filter to aggregate episodes in product pages."
                )
            else:
                raise ValueError("Invalid url.")


if __name__ == "__main__":
    main()
