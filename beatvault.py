#!/usr/bin/env python3
"""BeatVault — Download music from YouTube playlists as audio files."""

import sys
from pathlib import Path

from yt_dlp import YoutubeDL


DEFAULT_OUTPUT = "./music/"


def process_playlist(url, output_dir):
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(Path(output_dir) / '%(playlist_title)s' / '%(uploader)s - %(title)s.%(ext)s'),
        'ignoreerrors': True,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])


def main():
    urls = sys.argv[1:] if len(sys.argv) > 1 else []
    if not urls:
        url = input("Enter YouTube playlist URL: ").strip()
        if url:
            urls = [url]

    if not urls:
        print("No URL provided.")
        return 1

    Path(DEFAULT_OUTPUT).mkdir(parents=True, exist_ok=True)

    for url in urls:
        process_playlist(url, DEFAULT_OUTPUT)

    return 0


if __name__ == '__main__':
    sys.exit(main())
