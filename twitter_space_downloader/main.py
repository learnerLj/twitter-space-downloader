#!/usr/bin/env python3
"""
Twitter/X Space Downloader Python Script
Copyright (c) 2024 - The MIT License (MIT)
"""

import sys
import os
import re
from urllib.parse import urlparse

import click
import time
import signal
import asyncio
import aiohttp
import threading
from aiofiles import open as aio_open
import logging
import yt_dlp
import ffmpeg
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)
from rich.console import Console


class TwitterSpaceDownloader:
    """Twitter Space 下载器 - 异步高性能版本"""

    def __init__(
        self, max_concurrent=100, keep_temp=False, max_retries=3, audio_quality="low"
    ):
        self.max_concurrent = max_concurrent
        self.keep_temp = keep_temp
        self.max_retries = max_retries  # 添加重试次数参数
        self.audio_quality = audio_quality  # 添加音频质量参数

        # 状态管理
        self.temp_files = ["stream.m3u8"]
        self.download_cancelled = threading.Event()

        # 会话管理
        self.session = None
        self.connector = None
        self.cookies = None  # 添加cookie缓存

        # 进度统计
        self.stats = {
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "start_time": 0,
            "error_messages": [],
        }

        # Rich console实例
        self.console = Console()

        # 配置日志 - 彻底禁用aiohttp相关的错误日志
        logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
        logging.getLogger("aiohttp.client").setLevel(logging.CRITICAL)
        logging.getLogger("aiohttp.connector").setLevel(logging.CRITICAL)
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)
        # 禁用根日志记录器的SSL错误
        logging.getLogger().setLevel(logging.CRITICAL)

        # 初始化请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Origin": "https://x.com",
            "Referer": "https://x.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-CH-UA": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"macOS"',
        }

        # 初始化时获取cookie
        self._init_cookies()

    def _init_cookies(self):
        """初始化cookie"""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "cookiesfrombrowser": ("chrome",),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                cookies = ydl.cookiejar

                # 将cookie转换为aiohttp可用的格式
                self.cookies = {}
                for cookie in cookies:
                    # 只使用name和value，忽略其他属性
                    if cookie.domain.endswith("twitter.com") or cookie.domain.endswith(
                        "x.com"
                    ):
                        self.cookies[cookie.name] = cookie.value

            if self.cookies:
                self.console.print("✅ Cookie已从Chrome浏览器获取", style="green")
            else:
                self.console.print(
                    "⚠️ 未找到Twitter/X的Cookie，请确保已登录", style="yellow"
                )
        except Exception as e:
            self.console.print(f"⚠️ 获取Cookie失败: {e}", style="yellow")
            self.cookies = {}

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_session()

    async def create_session(self):
        """创建优化的aiohttp会话"""
        if self.session is None:
            # 配置连接器 - 优化连接管理，减少SSL错误
            self.connector = aiohttp.TCPConnector(
                limit=self.max_concurrent + 20,
                limit_per_host=min(self.max_concurrent, 50),  # 限制每个主机的连接数
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                # 优化连接设置
                keepalive_timeout=10,  # 减少keepalive时间
                timeout_ceil_threshold=5,
            )

            # 配置超时
            timeout = aiohttp.ClientTimeout(
                total=30,  # 增加总超时时间
                connect=10,  # 增加连接超时时间
                sock_read=15,  # 增加读取超时时间
            )

            # 配置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            # 创建会话
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
                headers=headers,
                raise_for_status=True,
            )

    async def close_session(self):
        """正确关闭会话和连接器 - 避免SSL错误"""
        if self.session:
            try:
                # 先关闭会话，不等待
                await self.session.close()

                # 给一点时间让连接自然关闭
                await asyncio.sleep(0.05)

            except Exception:
                # 完全静默处理所有关闭错误
                pass
            finally:
                self.session = None
                self.connector = None

    def cleanup_all_files(self):
        """清理临时文件"""
        try:
            # 清理m3u8文件
            for file in self.temp_files:
                if os.path.exists(file):
                    os.remove(file)
                    self.console.print(f"已删除: {file}")

        except Exception as e:
            self.console.print(f"清理文件时出错: {e}", style="bold red")

    def get_stream_url(self, space_url):
        """使用yt-dlp库获取流媒体URL"""
        self.console.print("正在获取流媒体URL...")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(space_url, download=False)

                # 查找音频流URL
                if "url" in info:
                    return info["url"]
                elif "formats" in info:
                    # 寻找最佳音频格式
                    for fmt in info["formats"]:
                        if fmt.get("acodec") != "none" and fmt.get("vcodec") == "none":
                            return fmt["url"]
                    # 如果没有纯音频，返回第一个格式的URL
                    if info["formats"]:
                        return info["formats"][0]["url"]

                raise Exception("无法找到流媒体URL")

        except Exception as e:
            self.console.print(f"获取流媒体URL失败: {e}", style="bold red")
            sys.exit(1)

    def get_filename(self, space_url):
        """使用yt-dlp库获取文件名"""
        self.console.print("正在获取文件名...")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "outtmpl": "%(upload_date)s - %(uploader_id)s.%(title)s.%(id)s.%(ext)s",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(space_url, download=False)

                # 构建文件名
                upload_date = info.get("upload_date", "unknown")
                uploader_id = info.get("uploader_id", "unknown")
                title = info.get("title", "untitled")
                video_id = info.get("id", "unknown")

                # 根据质量设置选择文件扩展名
                ext = "aac" if self.audio_quality == "fastest" else "mp3"

                # 清理文件名中的非法字符 - 根据质量选择格式
                filename = f"{upload_date} - {uploader_id}.{title}.{video_id}.{ext}"
                filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

                return filename

        except Exception as e:
            self.console.print(f"获取文件名失败: {e}", style="bold red")
            sys.exit(1)

    async def download_m3u8(self, stream_url, output_file="stream.m3u8"):
        """异步下载m3u8播放列表文件"""
        self.console.print(f"正在下载播放列表: {stream_url}")

        try:
            # 使用cookie发送请求
            async with self.session.get(
                stream_url, cookies=self.cookies, headers=self.headers
            ) as response:
                content = await response.text()

                async with aio_open(output_file, "w", encoding="utf-8") as f:
                    await f.write(content)

            self.console.print(f"播放列表已保存到: {output_file}")
            return True
        except Exception as e:
            self.console.print(f"下载播放列表失败: {e}", style="bold red")
            return False

    def extract_segment_urls(self, m3u8_file, stream_path):
        """从m3u8文件中提取所有音频片段URL"""
        try:
            with open(m3u8_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取所有.aac文件名
            pattern = r"^([^.#]+\.aac)$"
            aac_files = re.findall(pattern, content, flags=re.MULTILINE)

            # 构建完整URL列表
            segment_urls = []
            for aac_file in aac_files:
                full_url = f"{stream_path}{aac_file}"
                segment_urls.append((full_url, aac_file))

            return segment_urls
        except Exception as e:
            self.console.print(f"提取片段URL失败: {e}", style="bold red")
            return []

    async def download_single_segment(self, url_filename_tuple, semaphore):
        """异步下载单个音频片段到内存"""
        url, filename = url_filename_tuple
        max_retries = self.max_retries  # 使用类属性中的max_retries

        # 使用信号量控制并发数
        async with semaphore:
            # 检查是否已被取消
            if self.download_cancelled.is_set():
                return ("cancelled", filename, None)

            for attempt in range(max_retries):
                # 每次重试前都检查取消状态
                if self.download_cancelled.is_set():
                    return ("cancelled", filename, None)

                try:
                    # 为单个请求设置更长的超时时间
                    timeout = aiohttp.ClientTimeout(total=30, connect=10)
                    async with self.session.get(
                        url, timeout=timeout, cookies=self.cookies, headers=self.headers
                    ) as response:
                        # 将数据读取到内存中
                        data = bytearray()
                        async for chunk in response.content.iter_chunked(8192):
                            if self.download_cancelled.is_set():
                                return ("cancelled", filename, None)
                            data.extend(chunk)

                    # 返回成功结果和数据
                    return ("success", filename, bytes(data))

                except Exception as e:
                    if self.download_cancelled.is_set():
                        return ("cancelled", filename, None)

                    # 根据重试次数递增等待时间，但不打印重试信息
                    if attempt < max_retries - 1:
                        wait_time = 0.5 * (attempt + 1)  # 0.5s, 1.0s, 1.5s
                        await asyncio.sleep(wait_time)
                    else:
                        # 收集错误信息
                        error_msg = f"{filename}: {str(e)[:50]}..."
                        if len(self.stats["error_messages"]) < 5:
                            self.stats["error_messages"].append(error_msg)
                        return ("failed", filename, None)

            return ("failed", filename, None)

    async def download_segments(self, m3u8_file, stream_path):
        """使用异步协程并发下载音频片段到内存"""
        self.console.print("正在提取音频片段URL...")
        segment_urls = self.extract_segment_urls(m3u8_file, stream_path)

        if not segment_urls:
            self.console.print("未找到音频片段", style="bold red")
            return None

        self.console.print(
            f"找到 [bold blue]{len(segment_urls)}[/bold blue] 个音频片段，开始异步高速下载..."
        )
        self.console.print(
            f"使用 [bold green]{self.max_concurrent}[/bold green] 个并发连接"
        )
        self.console.print("💡 按 Ctrl+C 可随时停止下载\n")

        # 重置统计
        self.stats = {
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "start_time": time.time(),
            "error_messages": [],
        }

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # 用于存储下载结果的字典，按文件名排序
        segment_data = {}

        try:
            # 创建Rich进度条
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TextColumn(
                    "✅{task.fields[success]} ❌{task.fields[failed]} ⚠️{task.fields[cancelled]}"
                ),
                TextColumn("⚡{task.fields[speed]:.1f}/s"),
                TimeElapsedColumn(),
                console=self.console,
                transient=False,
            ) as progress:

                # 添加下载任务到进度条
                task = progress.add_task(
                    "下载音频片段",
                    total=len(segment_urls),
                    success=0,
                    failed=0,
                    cancelled=0,
                    speed=0.0,
                )

                # 创建所有下载任务 - 使用asyncio.create_task创建真正的Task对象
                tasks = [
                    asyncio.create_task(
                        self.download_single_segment(segment, semaphore)
                    )
                    for segment in segment_urls
                ]

                # 使用as_completed处理完成的任务
                for task_coro in asyncio.as_completed(tasks):
                    if self.download_cancelled.is_set():
                        self.console.print(
                            "\n⚠️  正在取消剩余下载任务...", style="bold yellow"
                        )
                        # 取消所有未完成的任务
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        break

                    try:
                        result = await task_coro
                        status, filename, data = result

                        if status == "success":
                            self.stats["completed"] += 1
                            segment_data[filename] = data
                        elif status == "cancelled":
                            self.stats["cancelled"] += 1
                        else:
                            self.stats["failed"] += 1

                        # 计算速度
                        elapsed = time.time() - self.stats["start_time"]
                        total_processed = (
                            self.stats["completed"]
                            + self.stats["failed"]
                            + self.stats["cancelled"]
                        )
                        speed = total_processed / elapsed if elapsed > 0 else 0

                        # 更新进度条
                        progress.update(
                            task,
                            completed=total_processed,
                            success=self.stats["completed"],
                            failed=self.stats["failed"],
                            cancelled=self.stats["cancelled"],
                            speed=speed,
                        )

                    except asyncio.CancelledError:
                        self.stats["cancelled"] += 1

                # 等待所有被取消的任务完成清理
                if self.download_cancelled.is_set():
                    # 给一点时间让取消的任务完成清理
                    await asyncio.sleep(0.1)
                    # 收集所有被取消的任务结果
                    for task_obj in tasks:
                        if task_obj.done() and not task_obj.cancelled():
                            try:
                                result = task_obj.result()
                                if result[0] == "cancelled":
                                    self.stats["cancelled"] += 1
                            except:
                                pass

            # 换行并显示最终结果
            elapsed = time.time() - self.stats["start_time"]
            speed = len(segment_urls) / elapsed if elapsed > 0 else 0

            self.console.print(
                f"\n📊 下载完成: [green]✅ {self.stats['completed']}[/green] 成功, [red]❌ {self.stats['failed']}[/red] 失败, [yellow]⚠️ {self.stats['cancelled']}[/yellow] 取消"
            )
            self.console.print(
                f"⏱️  总耗时: {int(elapsed//60):02d}:{int(elapsed%60):02d}, 平均速度: {speed:.1f} 片段/秒"
            )

            # 显示错误信息（如果有）
            if self.stats["error_messages"]:
                self.console.print(f"\n❌ 部分下载失败的原因:", style="bold red")
                for i, error in enumerate(self.stats["error_messages"][:3], 1):
                    self.console.print(f"   {i}. {error}")
                if len(self.stats["error_messages"]) > 3:
                    self.console.print(
                        f"   ... 还有 {len(self.stats['error_messages']) - 3} 个错误"
                    )

            if self.download_cancelled.is_set():
                return None

            if self.stats["failed"] > 0:
                self.console.print(
                    f"\n⚠️  有 {self.stats['failed']} 个片段下载失败，可能影响最终音频质量",
                    style="bold yellow",
                )

            # 按照原始顺序排序片段数据
            ordered_data = []
            original_filenames = [filename for _, filename in segment_urls]
            for filename in original_filenames:
                if filename in segment_data:
                    ordered_data.append(segment_data[filename])
                else:
                    # 如果某个片段失败了，用空数据占位
                    self.console.print(
                        f"⚠️  片段 {filename} 缺失，用静音替代", style="yellow"
                    )
                    ordered_data.append(b"")

            return ordered_data

        except Exception as e:
            self.console.print(f"\n❌ 异步下载过程中发生错误: {e}", style="bold red")
            self.download_cancelled.set()
            raise

    def merge_segments(self, segment_data_list, output_filename):
        """使用ffmpeg-python库从内存数据合并音频片段"""
        self.console.print(
            f"\n🔄 正在合并 [bold blue]{len(segment_data_list)}[/bold blue] 个音频片段..."
        )

        try:
            # 将所有音频数据连接成一个大的字节流
            combined_data = b"".join(segment_data_list)
            total_size = len(combined_data)
            self.console.print(
                f"数据大小: [bold cyan]{total_size / 1024 / 1024:.1f} MB[/bold cyan]"
            )

            # 获取CPU核心数用于多线程
            import multiprocessing

            cpu_count = multiprocessing.cpu_count()

            # 根据质量等级设置不同的编码参数
            quality_settings = {
                "fastest": {
                    "bitrate": None,
                    "preset": None,
                    "description": "最快速度(AAC格式,无转换)",
                    "extra_params": [],
                    "format": "aac",
                    "codec": "copy",  # 直接复制，无需重新编码
                },
                "low": {
                    "bitrate": "64k",
                    "preset": "ultrafast",
                    "description": "低质量(64kbps,语音优化)",
                    "extra_params": ["-ac", "1"],  # 单声道，进一步加速
                    "format": "mp3",
                    "codec": "libmp3lame",
                },
                "medium": {
                    "bitrate": "128k",
                    "preset": "veryfast",
                    "description": "中等质量(128kbps)",
                    "extra_params": [],
                    "format": "mp3",
                    "codec": "libmp3lame",
                },
                "high": {
                    "bitrate": "192k",
                    "preset": "fast",
                    "description": "高质量(192kbps)",
                    "extra_params": [],
                    "format": "mp3",
                    "codec": "libmp3lame",
                },
                "highest": {
                    "bitrate": "320k",
                    "preset": "medium",
                    "description": "最高质量(320kbps)",
                    "extra_params": [],
                    "format": "mp3",
                    "codec": "libmp3lame",
                },
            }

            settings = quality_settings.get(self.audio_quality, quality_settings["low"])
            self.console.print(
                f"音频质量: [bold yellow]{settings['description']}[/bold yellow]"
            )
            self.console.print(
                f"使用 [bold green]{cpu_count}[/bold green] 线程加速转换"
            )

            # 使用ffmpeg-python库处理音频
            input_stream = ffmpeg.input("pipe:", format="aac")

            if settings["codec"] == "copy":
                # 最快模式：直接复制AAC，无需重新编码
                self.console.print(
                    "🚀 [bold green]使用直接复制模式，无需转换![/bold green]"
                )
                output_stream = ffmpeg.output(
                    input_stream, output_filename, acodec="copy", f="adts"  # AAC格式
                )
            else:
                # 需要重新编码为MP3
                # 构建FFmpeg输出参数
                output_params = {
                    "acodec": settings["codec"],
                    "audio_bitrate": settings["bitrate"],
                    "preset": settings["preset"],
                    "threads": cpu_count,  # 多线程
                    "q:a": (
                        "9" if self.audio_quality == "low" else "2"
                    ),  # 低质量用更快的质量设置
                }

                # 添加额外参数（如单声道）
                if settings["extra_params"]:
                    for i in range(0, len(settings["extra_params"]), 2):
                        param_key = settings["extra_params"][i].lstrip("-")
                        param_value = settings["extra_params"][i + 1]
                        output_params[param_key] = param_value

                output_stream = ffmpeg.output(
                    input_stream, output_filename, **output_params
                )

            process = output_stream.overwrite_output().run_async(
                pipe_stdin=True, pipe_stdout=True, pipe_stderr=True
            )

            # 将数据写入ffmpeg的stdin
            stdout, stderr = process.communicate(input=combined_data)

            # 检查返回码
            if process.returncode == 0:
                self.console.print(
                    f"✅ 合并完成，文件已保存: [bold green]{output_filename}[/bold green]"
                )
            else:
                self.console.print(
                    f"❌ 合并失败，返回码: {process.returncode}", style="bold red"
                )
                if stderr:
                    self.console.print(f"错误详情: {stderr.decode()}", style="red")
                raise Exception(f"ffmpeg退出码: {process.returncode}")

        except Exception as e:
            self.console.print(f"❌ 合并失败: {e}", style="bold red")
            raise

    def cleanup_files(self, m3u8_file, output_filename=None):
        """清理临时文件"""
        try:
            # 删除m3u8文件
            if os.path.exists(m3u8_file):
                os.remove(m3u8_file)

        except Exception as e:
            self.console.print(f"清理文件时出错: {e}", style="bold red")

    async def download_space(self, space_url):
        """下载Twitter Space的主要方法"""
        try:
            self.console.print("🚀 启动异步高速下载模式...")

            # 1. 获取流媒体URL
            stream_url = self.get_stream_url(space_url)

            # 2. 获取输出文件名
            output_filename = self.get_filename(space_url)

            # 3. 提取流媒体路径
            parsed_url = urlparse(stream_url)
            stream_path = f"{parsed_url.scheme}://{parsed_url.netloc}{os.path.dirname(parsed_url.path)}/"

            self.console.print(f"流媒体路径: [dim]{stream_path}[/dim]")

            # 4. 下载m3u8播放列表
            if not await self.download_m3u8(stream_url):
                return False

            # 5. 下载音频片段到内存
            segment_data = await self.download_segments("stream.m3u8", stream_path)
            if self.download_cancelled.is_set():
                self.console.print(
                    "⚠️  下载已被用户取消，正在清理缓存文件...", style="bold yellow"
                )
                # 清理缓存文件
                if not self.keep_temp:
                    self.cleanup_all_files()
                return False
            elif segment_data is None:
                self.console.print("⚠️  音频片段下载失败", style="bold yellow")
                return False
            elif len([data for data in segment_data if data]) == 0:
                self.console.print("⚠️  没有有效的音频数据", style="bold yellow")
                return False

            # 6. 从内存数据合并音频片段
            self.merge_segments(segment_data, output_filename)

            # 7. 清理临时文件
            if not self.keep_temp:
                self.cleanup_files("stream.m3u8", output_filename)

            return True

        except Exception as e:
            self.console.print(f"\n❌ 发生错误: {e}", style="bold red")
            # 发生错误时也清理缓存文件
            if not self.keep_temp:
                self.console.print("正在清理缓存文件...")
                self.cleanup_all_files()
            return False


# 全局下载器实例，用于信号处理
downloader_instance = None


def signal_handler(signum, frame):
    """处理用户中断信号"""
    global downloader_instance

    print("\n\n⚠️  检测到用户中断，正在停止所有下载任务...")

    if downloader_instance:
        downloader_instance.download_cancelled.set()
        # 不在这里清理文件，让main函数处理

    print("❌ 用户中断下载")
    # 不使用sys.exit()，而是设置标志让程序自然退出
    if downloader_instance:
        downloader_instance.download_cancelled.set()


@click.command()
@click.argument("space_url")
@click.option("--keep-temp", is_flag=True, help="保留临时文件")
@click.option(
    "--max-workers",
    "-w",
    type=int,
    default=100,
    help="并发连接数（默认100，推荐50-200）",
)
@click.option(
    "--max-retries", "-r", type=int, default=3, help="每个片段的最大重试次数（默认3次）"
)
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["fastest", "low", "medium", "high", "highest"]),
    default="low",
    help="音频质量: fastest(AAC,无转换), low(64k,快速), medium(128k), high(192k), highest(320k)",
)
def cli_main(space_url, keep_temp, max_workers, max_retries, quality):
    """Twitter/X Space Downloader - 异步高速版本

    下载Twitter Space音频为MP3格式。

    SPACE_URL: Twitter Space的URL地址
    """
    global downloader_instance
    downloader_instance = None

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not space_url:
        click.echo("❌ 请提供Twitter Space URL")
        sys.exit(1)

    # 性能提示
    if max_workers > 200:
        click.echo("⚠️  并发数过高可能被服务器限制，建议使用50-200之间的值")
    elif max_workers < 50:
        click.echo("💡 可以尝试增加并发数来提升速度，如: --max-workers 100")

    # 质量说明
    quality_info = {
        "fastest": "AAC格式 - 无转换，最快速度",
        "low": "64kbps - 语音优化，快速转换",
        "medium": "128kbps - 平衡质量和速度",
        "high": "192kbps - 高质量音频",
        "highest": "320kbps - 最高质量，转换较慢",
    }
    click.echo(f"🎵 音频质量: {quality_info[quality]}")

    async def run_download():
        global downloader_instance
        try:
            # 创建下载器实例
            downloader_instance = TwitterSpaceDownloader(
                max_concurrent=max_workers,
                keep_temp=keep_temp,
                max_retries=max_retries,
                audio_quality=quality,
            )

            # 使用异步上下文管理器
            async with downloader_instance as downloader:
                success = await downloader.download_space(space_url)
                if not success or downloader.download_cancelled.is_set():
                    if downloader.download_cancelled.is_set():
                        click.echo("\n⚠️  下载被用户取消")
                        # 确保清理缓存文件
                        if not keep_temp:
                            click.echo("正在清理剩余缓存文件...")
                            downloader.cleanup_all_files()
                    return False

            return True

        except KeyboardInterrupt:
            click.echo("\n\n⚠️  检测到用户中断，正在清理缓存文件...")
            if downloader_instance and not keep_temp:
                downloader_instance.cleanup_all_files()
            return False
        except Exception as e:
            click.echo(f"\n❌ 发生错误: {e}")
            if downloader_instance and not keep_temp:
                click.echo("正在清理缓存文件...")
                downloader_instance.cleanup_all_files()
            return False

    try:
        success = asyncio.run(run_download())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n❌ 程序被中断")
        sys.exit(1)


if __name__ == "__main__":
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\n❌ 程序被中断")
        sys.exit(1)
