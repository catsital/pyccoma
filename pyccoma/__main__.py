#!/usr/bin/env python

import argparse

import re
import os
import logging
from getpass import getpass
from itertools import chain
from typing import Optional, Union, Tuple, List

from pyccoma.pyccoma import Scraper
from pyccoma.helpers import create_tags, valid_url, is_episode_url
from pyccoma.urls import history_url, bookmark_url, purchase_url

log = logging.getLogger("pyccoma.cli")
pyccoma = Scraper()

def main() -> None:
    try:
        parser = construct_parser()
        args = parser.parse_args()
        url = args.url

        if args.format:
            pyccoma.format = args.format

        if args.etype:
            if 'volume' in args.etype or 'episode' in args.etype:
                pyccoma.manga = args.etype[0]
                pyccoma.smartoon = args.etype[1]
            else:
                parser.error("Invalid type.")

        if args.omit_author:
            pyccoma.omit_author = args.omit_author

        if not args.range and not 'viewer' in args.url and args.filter == 'custom':
            parser.error(
                "Use --filter custom along with --range."
            )
        elif (args.range and not args.filter) or (args.range and args.filter in ('min', 'max', 'all')):
            log.warning("Overriding --filter={0} to parse custom.".format(args.filter))
            args.filter = 'custom'

        password = ""

        if args.email:
            if not password:
                password = getpass()

            pyccoma.login(args.email, password)

        if args.url and args.filter:
            if args.url[0] in ('history', 'bookmark', 'purchase') and pyccoma.is_login:
                if args.url[0] in history_url:
                    url = pyccoma.get_history().values()
                    print("Parsing ({0}) items from your history library.".format(len(url)))

                elif args.url[0] in bookmark_url:
                    url = pyccoma.get_bookmark().values()
                    print("Parsing ({0}) items from your bookmark library.".format(len(url)))

                elif args.url[0] in purchase_url:
                    url = pyccoma.get_purchase().values()
                    print("Parsing ({0}) items from your purchase library.".format(len(url)))

                for index, item in enumerate(url):
                    log.info(f"{index + 1}) {item}")

            elif args.url[0] in ('history', 'bookmark', 'purchase') and not pyccoma.is_login:
                parser.error("Login required.")

            elif "viewer" in args.url[0]:
                parser.error(
                    "There is nothing to aggregate. You should only use "
                    "--filter on a product page or your library."
                )

        if valid_url(str(args.url)):
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
            parser.error(
                "Invalid url."
            )

    except Exception:
        parser.error(
            "Exception on main."
        )

def construct_parser() -> None:
    parser = argparse.ArgumentParser(
        prog="pyccoma",
        description="Scrape and download from Piccoma.",
        epilog="Report bugs and make feature requests at "
            "https://github.com/catsital/pyccoma/issues",
        add_help=False,
    )

    required = parser.add_argument_group("Required options")
    required.add_argument(
        "url",
        nargs="*",
        help="Link to an episode or product. If using --filter, use: history, "
            "bookmark, or purchase as shorthand to scrape respective libraries."
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
        help="Format: png, jpeg, jpg, bmp (Default: png)"
    )
    optional.add_argument(
        "--omit-author",
        dest='omit_author',
        action='store_true',
        default=False,
        help="Omit author(s) in title naming scheme."
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
        nargs=2,
        metavar=("MANGA", "SMARTOON"),
        default=["volume", "episode"],
        help="Preferred episode type to scrape manga and smartoon when "
            "agrregating your library. (Default: manga=volume, smartoon=episode)"
    )
    filter.add_argument(
        "--filter",
        type=str,
        help="Filter to use when scraping manga and smartoon from your library. "
            "Can be either: min, max, all, or custom with --range. Requires login."
    )
    filter.add_argument(
        "--range",
        type=int,
        nargs=2,
        metavar=("START", "END"),
        help="Range to use when scraping manga and smartoon episodes."
    )
    filter.add_argument(
        "--include",
        type=include,
        default="episode",
        help="Arguments to include when parsing your library: is_purchased, is_free, "
            "is_already_read, is_limited_read, is_limited_free"
    )
    filter.add_argument(
        "--exclude",
        type=exclude,
        default="",
        help="Arguments to exclude when parsing your library: is_purchased, is_free, "
            "is_already_read, is_limited_read, is_limited_free"
    )

    info = parser.add_argument_group("Info")
    info.add_argument("-h", "--help", action="help", help="Show this help message and exit."),
    info.add_argument("-v", "--version", action="version", help="Show program version.", version="%(prog)s 0.2.0")

    return parser

def include(value: str) -> str:
    try:
        include = create_tags(value).replace("&", " and ").replace("|", " or ")
        return include
    except Exception:
        raise argparse.ArgumentTypeError('Specify type in this format: "is_free|is_already_read"')

def exclude(value: str) -> str:
    try:
        exclude = create_tags(value).replace("&", " and ").replace("|", " or ")
        return exclude
    except Exception:
        raise argparse.ArgumentTypeError('Specify type in this format: "is_free&is_already_read"')

def fetch(
    url: List[str],
    mode: Optional[str] = None,
    range: Optional[Tuple[int, int]] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    output: Optional[str] = None
) -> None:
    try:
        if mode:
            if not range:
                range = (0, 0)
            flags = {
                'min': '[episode[0] for episode in episodes if episode]',
                'max': '[episode[-1] for episode in episodes if episode]',
                'all': 'list(chain.from_iterable(episodes))',
                'custom': f"list(chain.from_iterable(episodes))[{range[0]}:{range[1]}]",
            }

            exclude = ' {0}not ({1})'.format('and ' if include else '', exclude)

            episodes = [[episode['url'] for episode in pyccoma.get_list(title).values()
                if eval((include) + (exclude))] for title in url]

            episodes = eval(flags[mode])
            episodes_total = len(episodes)

            print(f"Fetching ({episodes_total}) episodes.")

            for index, episode in enumerate(episodes):
                log.info(f"\nFetching {episode} ({index+1}/{episodes_total})")
                pyccoma.fetch(episode, output)

        else:
            for index, link in enumerate(url):
                if is_episode_url(link):
                    log.info(f"\nFetching {link} ({index+1}/{len(url)})")
                    pyccoma.fetch(link, output)
                else:
                    log.error("Use --filter to aggregate episodes in product pages.")

    except Exception as error:
        log.debug(error)
        log.error("Exiting the program.")

if __name__ == "__main__":
    main()
