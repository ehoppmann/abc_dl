# abc_dl
Triple J radio show downloader

Downloads radio programs from ABC (e.g. Triple J / Double J) and saves them in their native format (m4a)

## Requirements
(tested on Mac OS with Python 3.6 installed with [brew](https://brew.sh))

1. Python3 with requests (and optionally tenacity) installed. Call `pip3 install -r requirements.txt` while in this 
directory to install.
1. ffmpeg installed and available in your system PATH

## Usage
Running `./abc_dl.py <URL>` on the URL copied from the page of any ABC show's particular episode will download that
episode and save it to your Downloads directory. Optionally, the output directory can be passed as the second positional
argument following the URL.

```
usage: ./abc_dl.py [-h] [-s [SHOW_STR]] [-d [SHOW_DATE]]
                   [-mins [SHOW_MINUTES]]
                   [url] [output_dir]

positional arguments:
  url                   The page URL containing the program to download
  output_dir            Where the output file will be written to, by default
                        ~/Downloads

optional arguments:
  -h, --help            show this help message and exit
  -s [SHOW_STR], --show_str [SHOW_STR]
                        Instead of providing `url`, you can instead pass the
                        show stream string (e.g. fns for Friday Night Shuffle)
                        along with the show date and show number, and the CDN
                        download URLs will be constructed from these
  -d [SHOW_DATE], --show_date [SHOW_DATE]
                        Only needed if not passing `url`, A string
                        representing the date of the show, e.g. 2018-05-18 for
                        May 18th.
  -mins [SHOW_MINUTES], --show_minutes [SHOW_MINUTES]
                        Only needed if not passing `url`, number of minutes in
                        the show
```

### Example
Download the 5-18-18 episode of Friday Night Shuffle by url:

`./abc_dl.py http://www.abc.net.au/triplej/programs/friday-night-shuffle/friday-night-shuffle/9755372`

Downloading the same episode without a URL is possible by providing the show string (fns) and date.
We can skip passing in the minutes for the show (60*3 = 180) since that's the default value:

`./abc_dl.py -s fns -d 2018-05-18`