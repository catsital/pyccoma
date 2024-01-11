# Pyccoma

[![Downloads](https://pepy.tech/badge/pyccoma)](https://pepy.tech/project/pyccoma)
[![Latest GitHub release](https://img.shields.io/github/tag/catsital/pyccoma.svg)](https://github.com/catsital/pyccoma/releases/latest)
[![Latest PyPI release](https://img.shields.io/pypi/v/pyccoma)](https://pypi.org/project/pyccoma/)
[![License](https://badgen.net/github/license/catsital/pyccoma)](https://github.com/catsital/pyccoma/blob/main/LICENSE)

Directly download smartoon, manga, and novels from [Piccoma Japan](https://jp.piccoma.com/web/) and [Piccoma France](https://fr.piccoma.com/fr/).

![pyccoma](https://user-images.githubusercontent.com/18095632/177802537-1698ba0a-266c-4ff7-b4ae-d288c68de2b1.gif)

## Prerequisites
* Python 3.11

## Install

```bash
$ pip install pyccoma
```

## Getting Started

### Using the command-line utility

To download a single episode, simply use:

```bash
$ pyccoma https://piccoma.com/web/viewer/103981/2646730
```

You can also pass multiple links (separated by whitespace) to download in one go, then use the **--archive** option to output to a cbz archive.

```bash
$ pyccoma https://piccoma.com/web/viewer/60171/1575237 https://piccoma.com/web/viewer/8195/1185884 --archive
```

Use the option **--region** to switch between Piccoma Japan (default) and Piccoma France.

```bash
$ pyccoma https://piccoma.com/fr/viewer/49/2946 --region fr
```

Access purchased episodes from your library by logging in using the **--email** option.

```bash
$ pyccoma purchase --region fr --filter all --include is_purchased --email foo@bar.com
$ pyccoma purchase --region jp --filter all --include is_purchased --email foo@bar.com
```

Read more about the available CLI options on [the next section](https://github.com/catsital/pyccoma#options) below. You can also see more examples [here](https://github.com/catsital/pyccoma#examples) on how to aggregate and batch download using the command-line utility.

### Using Python shell

Import the `Pyccoma` class according to their region.

|    Module    |       Description        |
|--------------|--------------------------|
| `pyccoma.jp` |      Piccoma Japan       |
| `pyccoma.fr` |      Piccoma France      |

Create a `Pyccoma` instance and use `fetch` to scrape and download images from a viewer page.

```python
>>> from pyccoma.jp import Pyccoma
>>> jp = Pyccoma()
>>> jp.fetch('https://piccoma.com/web/viewer/8195/1185884')

Title: ひげを剃る。そして女子高生を拾う。(しめさば ぶーた 足立いまる)
Episode: 第1話 失恋と女子高生 (1)
  |███████████████████████████████████████████████████████████| 100.0% (14/14)
Elapsed time: 00:00:17

>>> from pyccoma.fr import Pyccoma
>>> fr = Pyccoma()
>>> fr.fetch('https://piccoma.com/fr/viewer/49/2944')

Title: Roxana (BAEK JI-YEON Juniljus Kin)
Episode: #1 Il est mon seul espoir de survie
  |███████████████████████████████████████████████████████████| 100.0% (80/80)
Elapsed time: 00:00:47
```

You can use `login` to have access to rental or paywalled episodes from your own library.

```python
>>> jp.login(email, password)
>>> jp.fetch('https://piccoma.com/web/viewer/s/4995/1217972', 'output_dir')

Title: かぐや様は告らせたい～天才たちの恋愛頭脳戦～(赤坂アカ)
Episode: 第135話
  |███████████████████████████████████████████████████████████| 100.0% (20/20)
Elapsed time: 00:00:23
```

## Options

### Required

|          Option           |              Description           |          Examples                                      |
|---------------------------|------------------------------------|--------------------------------------------------------|
|          url              | Must be a valid url                | `https://piccoma.com/web/product/4995/episodes?etype=V`, `https://piccoma.com/web/product/12482/episodes?etype=E`, `https://piccoma.com/web/viewer/12482/631201`, `https://piccoma.com/fr/product/volume/109`, `https://piccoma.com/fr/product/episode/231`, `bookmark`, `history`, `purchase`                       |

### Locale

|     Option     |                Description                   |                  Examples                   |
|----------------|----------------------------------------------|---------------------------------------------|
|   --region     | Select which service to use                  | `Jp` (Piccoma Japan), `Fr` (Piccoma France) |

### Optional

|     Option      |              Description                  |                          Examples                                      |
|-----------------|-------------------------------------------|------------------------------------------------------------------------|
| -o, --output    | Local directory to save downloaded images | `D:/piccoma/` (absolute path), `/piccoma/download/` (relative path)    |
| -f, --format    | Image format                              | `jpeg`, `jpg`, `gif`, `bmp`, `png` (default)                           |
| -p, --pad       | Pad page numbers with leading zeroes      | `0` (default)                                                          |
| --archive       | Download as cbz archive                 |                                                                        |
| --omit-author   | Omit author names from titles             |                                                                        |

### Retry

|     Option      |              Description                  |                          Examples                                      |
|-----------------|-------------------------------------------|------------------------------------------------------------------------|
| --retry-count   | Number of download retry attempts when error occurred | `3` (default)                                              |
| --retry-interval| Delay between each retry attempt (in seconds) | `1` (default)                                                      |

### Login

|          Option           |              Description                                                                    |          Examples           |
|---------------------------|---------------------------------------------------------------------------------------------|-----------------------------|
|   --email                 | Your registered email address; this does not support OAuth authentication                   | `foo@bar.com`               |

### Filter

|  Option   |                    Description                         |                         Examples                               |
|-----------|--------------------------------------------------------|----------------------------------------------------------------|
| --etype   | Preferred episode type to scrape manga, smartoon, and novel when scraping `history`, `bookmark`, `purchase`; takes in three arguments, the first one for manga, the second for smartoon, and the last one for novel  | `volume` to scrape for volumes, `episode` to scrape for episodes |
| --filter  | Filter to use when scraping episodes from a product page or your library | `min`, `max`, `all`, or `custom` by defining --range. Use `min` to scrape for the first item, `max` for the last item, `all` to scrape all items, and `custom` to scrape for a specific index range |
| --range   | Range to use when scraping episodes; takes in two arguments, start and end; will always override --filter to parse custom, if omitted or otherwise | `0 10` will scrape the first up to the tenth episode |
| --include | Status arguments to include when parsing a library or product; can parse in `\|` and `&` operators as conditionals, see [use cases below](https://github.com/catsital/pyccoma#examples) | `is_purchased`, `is_free`, `is_zero_plus`, `is_already_read`, `is_read_for_free`, `is_wait_until_free` |
| --exclude | Status arguments to exclude when parsing a library or product; can parse in `\|` and `&` operators as conditionals, see [use cases below](https://github.com/catsital/pyccoma#examples) | `is_purchased`, `is_free`, `is_zero_plus`, `is_already_read`, `is_read_for_free`, `is_wait_until_free` |

### Logging

|          Option           |              Description           |          Examples                                      |
|---------------------------|------------------------------------|--------------------------------------------------------|
|   -l, --loglevel          | Set the log message threshold      | `debug`, `info` (default), `warning`, `error`, `none`  |

## Examples

Use the **--include** and **--exclude** options in the command-line utility to narrow down which items are included in an aggregation.

|         Argument         |                             Description                            |
|--------------------------|--------------------------------------------------------------------|
|       **is_free**        | Free-to-access volumes/episodes                                    |
|   **is_wait_until_free**   | Episodes that can be accessed by waiting/using free pass         |
|   **is_read_for_free**   | Episodes that are accessed using free pass                         |
|     **is_purchased**     | Purchased volumes/episodes                                         |
|     **is_zero_plus**     | Free-to-access episodes                                            |
|   **is_already_read**    | Items that have been accessed before; formatted as grayed-out rows |

### Aggregating and downloading in batch

* Downloading all free episodes in a single product page:

```bash
$ pyccoma https://piccoma.com/web/product/67171/episodes?etype=E --filter all --include is_free
```

* Downloading all free episodes across multiple products:

```bash
$ pyccoma https://piccoma.com/web/product/5523/episodes?etype=E https://piccoma.com/web/product/23019/episodes?etype=E --filter all --include is_free
```

* Downloading all first episodes across multiple products:

```bash
$ pyccoma https://piccoma.com/web/product/6575/episodes?etype=E https://piccoma.com/web/product/41993/episodes?etype=E --filter min
```

* Downloading using custom with range:

```bash
$ pyccoma https://piccoma.com/web/product/16070/episodes?etype=E --filter custom --range 1 5
```

## Disclaimer

Pyccoma was made for the sole purpose of helping users download media from [Piccoma](https://piccoma.com) for offline consumption. This is for private use only, do not use this tool to promote piracy.
