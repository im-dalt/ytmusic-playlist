#!/usr/bin/env python3
"""BeatVault — Download music from YouTube playlists as audio files."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from yt_dlp import YoutubeDL


HISTORY_FILE = Path("downloaded_songs.json")
DEFAULT_OUTPUT = "./music/"
QUALITY_MAP = {
    "low": 128,
    "medium": 192,
    "high": 320,
}
DEFAULT_QUALITY = "medium"


def _sanitize_path(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    return name or 'Unknown_Playlist'


def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def build_ydl_opts(output_dir, playlist_name, quality):
    q = QUALITY_MAP.get(quality, QUALITY_MAP[DEFAULT_QUALITY])
    safe_name = _sanitize_path(playlist_name)
    outtmpl = str(Path(output_dir) / safe_name / '%(uploader)s - %(title)s.%(ext)s')
    return {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': str(q)},
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            {'key': 'EmbedThumbnail'},
        ],
        'writethumbnail': True,
        'ignoreerrors': True,
    }


def process_playlist(url, output_dir, quality, history):
    with YoutubeDL({'quiet': True, 'ignoreerrors': True}) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        print(f"[ERROR] Could not retrieve playlist: {url}")
        return 0, 0, 1

    playlist_title = info.get('title', 'Unknown Playlist')
    entries = info.get('entries', [])
    if not entries:
        print(f"[INFO] No entries found in playlist: {playlist_title}")
        return 0, 0, 0

    print(f"\n[PLAYLIST] {playlist_title} ({len(entries)} videos)")

    to_download = []
    skipped = 0
    for entry in entries:
        if entry is None:
            continue
        vid = entry.get('id')
        title = entry.get('title', 'Unknown')
        if vid and vid in history:
            print(f"[SKIPPED] {title} — already downloaded")
            skipped += 1
        else:
            to_download.append(entry)

    if not to_download:
        print("[INFO] No new songs to download.")
        return 0, skipped, 0

    opts = build_ydl_opts(output_dir, playlist_title, quality)

    downloaded = 0
    failed = 0
    with YoutubeDL(opts) as ydl:
        for entry in to_download:
            video_url = entry.get('webpage_url')
            vid = entry.get('id')
            title = entry.get('title', 'Unknown')
            uploader = entry.get('uploader', 'Unknown')

            if not video_url or not vid:
                failed += 1
                continue

            ydl.download([video_url])
            history[vid] = {
                'title': title,
                'artist': uploader,
                'url': video_url,
                'download_date': datetime.now().isoformat(),
                'playlist_name': playlist_title,
            }
            save_history(history)
            print(f"[DOWNLOADED] {title}")
            downloaded += 1

    return downloaded, skipped, failed


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
    history = load_history()
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    for url in urls:
        d, s, f = process_playlist(url, DEFAULT_OUTPUT, DEFAULT_QUALITY, history)
        total_downloaded += d
        total_skipped += s
        total_failed += f

    print(f"\nDownloaded: {total_downloaded} | Skipped: {total_skipped} | Failed: {total_failed}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
