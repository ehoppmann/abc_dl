# abc_dl
Triple J radio show downloader

Downloads radio programs from ABC (e.g. Triple J / Double J) and saves them in their native format (m4a)

## Requirements
1. Python3 with requests (and optionally tenacity) installed. Call `pip3 install -r requirements.txt` while in this 
directory to install.
1. ffmpeg installed and available in your system PATH

## Usage
Running `./abc_dl.py <URL>` on the URL copied from the page of any ABC show's particular episode will download that
episode and save it to your Downloads directory. Optionally, the output directory can be passed as the second positional
argument following the URL.

```
usage: ./abc_dl.py [-h] url [output_dir]

positional arguments:
  url         The page URL containing the program to download
  output_dir  Where the output file will be written to, by default ~/Downloads

optional arguments:
  -h, --help  show this help message and exit
```

### Example
Download the 5-18-18 episode of Friday Night Shuffle:

`./abc_dl.py http://www.abc.net.au/triplej/programs/friday-night-shuffle/friday-night-shuffle/9755372`
