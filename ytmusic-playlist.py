#!/usr/bin/env python3
"""BeatVault — Download music from YouTube playlists as audio files."""

import argparse
import json
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

            try:
                ydl.download([video_url])
            except KeyboardInterrupt:
                save_history(history)
                raise
            except Exception as e:
                print(f"[FAILED] {title} — {e}")
                failed += 1
                continue

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


def print_summary(downloaded, skipped, failed):
    print("\n" + "=" * 40)
    print("DOWNLOAD SUMMARY")
    print("=" * 40)
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {failed}")
    print("=" * 40)


def list_songs(history):
    if not history:
        print("No songs have been downloaded yet.")
        return

    playlists = {}
    for vid, meta in history.items():
        playlist = meta.get('playlist_name', 'Unknown')
        playlists.setdefault(playlist, []).append((vid, meta))

    total = len(history)
    print(f"\nTotal songs: {total}")
    for playlist, songs in sorted(playlists.items()):
        print(f"\n  [{playlist}] ({len(songs)} songs)")
        for vid, meta in sorted(songs, key=lambda x: x[1].get('title', '')):
            title = meta.get('title', 'Unknown')
            artist = meta.get('artist', 'Unknown')
            date = meta.get('download_date', '')[:10]
            print(f"    {artist} - {title} (downloaded: {date})")


def search_songs(history, query):
    if not history:
        print("No songs have been downloaded yet.")
        return

    query_lower = query.lower()
    results = []
    for vid, meta in history.items():
        title = meta.get('title', '').lower()
        artist = meta.get('artist', '').lower()
        if query_lower in title or query_lower in artist:
            results.append((vid, meta))

    if not results:
        print(f"No results found for '{query}'.")
        return

    print(f"\nFound {len(results)} result(s) for '{query}':")
    for vid, meta in sorted(results, key=lambda x: x[1].get('title', '')):
        title = meta.get('title', 'Unknown')
        artist = meta.get('artist', 'Unknown')
        date = meta.get('download_date', '')[:10]
        print(f"  {artist} - {title} (downloaded: {date})")


def reset_history():
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
        print("[OK] Download history cleared.")
    else:
        print("[INFO] No history file found.")


def main():
    parser = argparse.ArgumentParser(
        description="BeatVault — Download music from YouTube playlists as audio files."
    )
    parser.add_argument('urls', nargs='*', help='YouTube playlist URL(s) to download')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'], default=DEFAULT_QUALITY,
                        help=f'Audio quality (default: {DEFAULT_QUALITY})')
    parser.add_argument('--output', default=DEFAULT_OUTPUT,
                        help=f'Output directory (default: {DEFAULT_OUTPUT})')
    parser.add_argument('--list', action='store_true', help='Display all downloaded songs')
    parser.add_argument('--reset', action='store_true', help='Clear download history')
    parser.add_argument('--search', metavar='QUERY', help='Search downloaded songs by title or artist')
    args = parser.parse_args()

    history = load_history()

    if args.list:
        list_songs(history)
        return

    if args.search:
        search_songs(history, args.search)
        return

    if args.reset:
        confirm = input("Are you sure you want to clear download history? (y/N): ")
        if confirm.lower() == 'y':
            reset_history()
        else:
            print("[INFO] Reset cancelled.")
        return

    urls = args.urls
    if not urls:
        url = input("Enter YouTube playlist URL: ").strip()
        if url:
            urls = [url]

    if not urls:
        print("No URL provided.")
        return 1

    Path(args.output).mkdir(parents=True, exist_ok=True)
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    try:
        for url in urls:
            d, s, f = process_playlist(url, args.output, args.quality, history)
            total_downloaded += d
            total_skipped += s
            total_failed += f
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Progress has been saved.")
        print_summary(total_downloaded, total_skipped, total_failed)
        return 130

    print_summary(total_downloaded, total_skipped, total_failed)
    return 0


if __name__ == '__main__':
    sys.exit(main())
