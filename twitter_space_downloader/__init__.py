"""
Twitter/X Space Downloader

高性能异步Twitter Space下载器，支持并发下载和自动合并。
"""

__version__ = "1.0.0"
__author__ = "Luo Jiahao"
__email__ = "luoshitou9@gmail.com"

from .main import TwitterSpaceDownloader

__all__ = ["TwitterSpaceDownloader"]
