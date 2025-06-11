# Twitter/X Space Downloader

高性能异步Twitter Space下载器，支持并发下载和自动合并。

## 功能特点

- 🚀 异步高速下载，支持100+并发连接
- 💾 内存流式处理，无临时文件
- 📦 使用Python库而非命令行工具，更稳定可靠
- 🔄 自动重试机制，提高下载成功率
- 📊 实时进度显示和统计信息
- 🧹 智能缓存清理，支持用户中断
- 🎵 自动合并音频片段为完整文件
- 🎶 智能音频质量选择，默认64kbps语音优化，可选高质量
- ⚡ 快速转换，默认低质量模式转换速度极快
- 🏃‍♂️ 超快模式：fastest选项直接保存AAC格式，无需转换
- 🔥 多线程FFmpeg加速，充分利用CPU性能
- 🔐 自动从Chrome获取cookie，支持认证内容下载
- 🌐 完整浏览器请求头模拟，提高下载成功率

## 系统要求

- Python 3.7+
- ffmpeg 二进制文件（用于音频合并）
- 网络连接

## 安装

### 使用pip安装（推荐）

```bash
pip install twitter-space-downloader
```

安装后，您可以在任何地方使用命令：

```bash
# 完整命令名
twitter-space-downloader "https://twitter.com/i/spaces/1234567890"

# 或使用简短别名
tsd "https://twitter.com/i/spaces/1234567890"
```

### 从源码安装

克隆仓库并安装：

```bash
git clone https://github.com/yourusername/twitter-space-downloader.git
cd twitter-space-downloader
pip install .
```

## 系统要求

- Python 3.7+
- ffmpeg 二进制文件（用于音频合并）

### 安装ffmpeg

**macOS (使用Homebrew)**：
```bash
brew install ffmpeg
```

**Ubuntu/Debian**：
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows**：
- 下载并安装 [FFmpeg](https://ffmpeg.org/download.html)
- 确保ffmpeg在系统PATH中

## 使用方法

### 基本用法

```bash
# 超快速下载（AAC格式，无转换，推荐用于快速预览）
twitter-space-downloader --quality fastest "https://twitter.com/i/spaces/1234567890"

# 默认低质量，快速转换，适合语音内容
twitter-space-downloader "https://twitter.com/i/spaces/1234567890"

# 或使用简短别名
tsd "https://twitter.com/i/spaces/1234567890"
```

### 高级选项

```bash
# 超快速模式（推荐用于长时间录音或快速预览）
twitter-space-downloader -q fastest "https://twitter.com/i/spaces/1234567890"

# 调整音频质量（默认low，快速转换）
twitter-space-downloader --quality medium "https://twitter.com/i/spaces/1234567890"
twitter-space-downloader -q high "https://twitter.com/i/spaces/1234567890"

# 调整并发数（默认100）
twitter-space-downloader --max-workers 150 "https://twitter.com/i/spaces/1234567890"

# 保留临时文件（主要是m3u8播放列表）
twitter-space-downloader --keep-temp "https://twitter.com/i/spaces/1234567890"

# 调整重试次数（默认3次）
twitter-space-downloader --max-retries 5 "https://twitter.com/i/spaces/1234567890"

# 组合选项使用
twitter-space-downloader -q high -w 200 -r 5 "https://twitter.com/i/spaces/1234567890"

# 查看帮助
twitter-space-downloader --help
```

### 参数说明

- `--quality, -q`: 音频质量选择
  - `fastest`: AAC格式 (推荐) - 无转换，最快速度，兼容性好
  - `low`: 64kbps (默认) - 语音优化，转换最快
  - `medium`: 128kbps - 平衡质量和速度
  - `high`: 192kbps - 高质量音频
  - `highest`: 320kbps - 最高质量，转换较慢
- `--max-workers, -w`: 并发下载连接数（推荐50-200，默认100）
- `--keep-temp`: 保留临时文件（仅m3u8播放列表文件）
- `--max-retries, -r`: 每个片段的最大重试次数（默认3次）

## 工作原理

1. 🔍 程序使用yt-dlp库提取Space的音频流信息
2. 📥 并发下载所有音频片段到内存（无临时文件）
3. 🔄 智能音频处理：
   - **fastest模式**: 直接保存AAC格式，无需转换（推荐）
   - **其他模式**: 多线程FFmpeg转换为MP3格式
4. 🧹 自动清理临时的m3u8播放列表文件

## 性能特点

- **内存流式处理**: 所有音频片段直接在内存中处理，避免磁盘I/O
- **零临时文件**: 不生成临时音频文件，只有m3u8播放列表
- **高并发**: 支持100+并发连接同时下载
- **智能重试**: 失败片段自动重试，不影响其他下载
- **多线程转换**: FFmpeg使用所有CPU核心加速音频转换
- **超快模式**: fastest选项直接复制AAC，转换时间接近0

### 中断处理

- 按 `Ctrl+C` 可随时停止下载
- 程序会自动清理临时的m3u8文件
- 内存中的数据会自动释放

## 性能优化

- **最快速度**: 使用 `--quality fastest` 获得最快下载体验（AAC格式）
- **网络较好**: 可增加 `--max-workers` 到150-200
- **网络不稳定**: 可减少到50-80
- **重试调整**: 根据网络情况调整 `--max-retries`
- **格式选择**: 
  - 快速预览或长录音：选择 `fastest` (AAC)
  - 需要MP3兼容性：选择 `low` 或 `medium`

## 故障排除

1. **安装依赖失败**: 确保Python版本3.7+，尝试使用虚拟环境
2. **ffmpeg未找到**: 确保ffmpeg已安装且在系统PATH中
3. **下载失败**: 检查Space URL是否正确，网络连接是否稳定
4. **内存不足**: 对于超长Space，可能需要足够的内存

## 许可证

MIT License - 详见 LICENSE 文件