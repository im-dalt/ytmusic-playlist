# BeatVault

Download music from YouTube playlists as audio files (MP3).

## Prerequisites

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) (must be installed separately and available in PATH)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Download a playlist (you'll be prompted for URL)
python beatvault.py

# Download one or more playlist URLs directly
python beatvault.py "https://youtube.com/playlist?list=..."

# Download multiple playlists
python beatvault.py "https://youtube.com/playlist?list=..." "https://youtube.com/playlist?list=..."

# Set audio quality
python beatvault.py --quality high "https://youtube.com/playlist?list=..."

# Custom output directory
python beatvault.py --output ./my_music/ "https://youtube.com/playlist?list=..."

# List all downloaded songs
python beatvault.py --list

# Search downloaded songs
python beatvault.py --search "song name"

# Reset download history
python beatvault.py --reset
```

## Audio Quality

| Flag      | Bitrate |
|-----------|---------|
| `--quality low`   | 128 kbps  |
| `--quality medium` (default) | 192 kbps  |
| `--quality high`  | 320 kbps  |

## Output Structure

```
music/
├── Playlist Name/
│   ├── Artist - Song Title.mp3
│   └── ...
└── ...
```

## Features

- Downloads only audio (no video files)
- Converts to MP3 via ffmpeg
- Embeds metadata: title, artist, cover art, upload date
- Tracks downloaded songs to avoid duplicates
- Groups downloads into playlist-named subfolders
- Supports multiple playlist URLs in a single run
- `--list`, `--search`, and `--reset` flags for history management
- Graceful error handling for private/age-restricted videos
- Ctrl+C safely saves progress

## Dependencies

- **yt-dlp** — YouTube downloading (listed in requirements.txt)
- **ffmpeg** — Audio conversion and metadata embedding (install separately)
