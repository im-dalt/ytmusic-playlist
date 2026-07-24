#!/usr/bin/env python3
"""BeatVault — Download music from YouTube playlists as audio files."""

import sys
from pathlib import Path

from yt_dlp import YoutubeDL


DEFAULT_OUTPUT = "./music/"
QUALITY_MAP = {
    "low": 128,
    "medium": 192,
    "high": 320,
}
DEFAULT_QUALITY = "medium"


def build_ydl_opts(output_dir, quality):
    q = QUALITY_MAP.get(quality, QUALITY_MAP[DEFAULT_QUALITY])
    return {
        'format': 'bestaudio/best',
        'outtmpl': str(Path(output_dir) / '%(playlist_title)s' / '%(uploader)s - %(title)s.%(ext)s'),
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': str(q)},
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            {'key': 'EmbedThumbnail'},
        ],
        'writethumbnail': True,
        'ignoreerrors': True,
    }


def process_playlist(url, output_dir, quality):
    opts = build_ydl_opts(output_dir, quality)
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
        process_playlist(url, DEFAULT_OUTPUT, DEFAULT_QUALITY)

    return 0


if __name__ == '__main__':
    sys.exit(main())
