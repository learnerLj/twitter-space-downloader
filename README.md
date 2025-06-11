# Twitter/X Space Downloader

High-performance asynchronous Twitter Space downloader with concurrent download and automatic merging.

## Features

- 🚀 Asynchronous high-speed download, supporting 100+ concurrent connections
- 💾 Memory streaming processing, no temporary files
- 📦 Uses Python libraries instead of command-line tools, more stable and reliable
- 🔄 Automatic retry mechanism, improving download success rate
- 📊 Real-time progress display and statistics
- 🧹 Smart cache cleanup, supports user interruption
- 🎵 Automatically merges audio segments into a complete file
- 🎶 Smart audio quality selection, default 64kbps voice optimization, optional high quality
- ⚡ Fast conversion, default low quality mode conversion speed is extremely fast
- 🏃‍♂️ Ultra-fast mode: fastest option directly saves AAC format, no conversion needed
- 🔥 Multi-threaded FFmpeg acceleration, fully utilizing CPU performance
- 🔐 Automatically gets cookies from Chrome, supports authenticated content download
- 🌐 Complete browser request header simulation, improving download success rate

## System Requirements

- Python 3.7+
- ffmpeg binary file (for audio merging)
- Network connection

## Installation

### Using pip (Recommended)

```bash
pip install twitter-space-downloader
```

After installation, you can use the command anywhere:

```bash
# Full command name
twitter-space-downloader "https://twitter.com/i/spaces/1234567890"

# Or use the short alias
tsd "https://twitter.com/i/spaces/1234567890"
```

### Installing from Source

Clone the repository and install:

```bash
git clone https://github.com/learnerlj/twitter-space-downloader.git
cd twitter-space-downloader
pip install .
```

## System Requirements

- Python 3.10+
- ffmpeg binary file (for audio merging)

### Installing ffmpeg

**macOS (using Homebrew)**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows**:
- Download and install [FFmpeg](https://ffmpeg.org/download.html)
- Ensure ffmpeg is in the system PATH

## Usage

### Basic Usage

```bash
# Ultra-fast download (AAC format, no conversion, recommended for quick preview)
twitter-space-downloader --quality fastest "https://twitter.com/i/spaces/1234567890"

# Default low quality, quick conversion, suitable for voice content
twitter-space-downloader "https://twitter.com/i/spaces/1234567890"

# Or use the short alias
tsd "https://twitter.com/i/spaces/1234567890"
```

### Advanced Options

```bash
# Ultra-fast mode (recommended for long recordings or quick preview)
twitter-space-downloader -q fastest "https://twitter.com/i/spaces/1234567890"

# Adjust audio quality (default low, quick conversion)
twitter-space-downloader --quality medium "https://twitter.com/i/spaces/1234567890"
twitter-space-downloader -q high "https://twitter.com/i/spaces/1234567890"

# Adjust concurrency (default 100)
twitter-space-downloader --max-workers 150 "https://twitter.com/i/spaces/1234567890"

# Keep temporary files (mainly m3u8 playback list)
twitter-space-downloader --keep-temp "https://twitter.com/i/spaces/1234567890"

# Adjust retry count (default 3 times)
twitter-space-downloader --max-retries 5 "https://twitter.com/i/spaces/1234567890"

# Combine options usage
twitter-space-downloader -q high -w 200 -r 5 "https://twitter.com/i/spaces/1234567890"

# View help
twitter-space-downloader --help
```

### Parameter Description

- `--quality, -q`: Audio quality selection
  - `fastest`: AAC format (recommended) - no conversion, fastest speed, good compatibility
  - `low`: 64kbps (default) - voice optimization, fastest conversion
  - `medium`: 128kbps - balanced quality and speed
  - `high`: 192kbps - high quality audio
  - `highest`: 320kbps - highest quality, slower conversion
- `--max-workers, -w`: Concurrent download connection count (recommended 50-200, default 100)
- `--keep-temp`: Keep temporary files (only m3u8 playback list file)
- `--max-retries, -r`: Maximum retry count for each segment (default 3 times)

## Work Principle

1. 🔍 Program uses yt-dlp library to extract audio stream information from Space
2. 📥 Concurrent download all audio segments to memory (no temporary files)
3. 🔄 Smart audio processing:
   - **fastest mode**: Directly save AAC format, no conversion needed (recommended)
   - **other modes**: Multi-threaded FFmpeg converts to MP3 format
4. 🧹 Automatically clean temporary m3u8 playback list files

## Performance Features

- **Memory streaming processing**: All audio segments are processed directly in memory, avoiding disk I/O
- **Zero temporary files**: No temporary audio files are generated, only m3u8 playback list
- **High concurrency**: Supports 100+ concurrent connections to download simultaneously
- **Smart retry**: Failed segments automatically retry, without affecting other downloads
- **Multi-threaded conversion**: FFmpeg uses all CPU cores to accelerate audio conversion
- **Ultra-fast mode**: fastest option directly copies AAC, conversion time is close to 0

### Interrupt Handling

- Press `Ctrl+C` at any time to stop download
- Program will automatically clean temporary m3u8 files
- Data in memory will be automatically released

## Performance Optimization

- **Fastest speed**: Use `--quality fastest` to get the fastest download experience (AAC format)
- **Good network**: Can increase `--max-workers` to 150-200
- **Unstable network**: Can reduce to 50-80
- **Retry adjustment**: Adjust `--max-retries` according to network conditions
- **Format selection**: 
  - Quick preview or long recording: Choose `fastest` (AAC)
  - Need MP3 compatibility: Choose `low` or `medium`

## Troubleshooting

1. **Installation dependency failure**: Ensure Python version 3.7+, try using virtual environment
2. **ffmpeg not found**: Ensure ffmpeg is installed and in the system PATH
3. **Download failure**: Check if Space URL is correct and network connection is stable
4. **Memory insufficient**: For very long Space, enough memory may be required

## License

MIT License - See LICENSE file