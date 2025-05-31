#!/usr/bin/env python3
"""
构建和发布脚本

使用方法:
python build_and_publish.py --build      # 只构建
python build_and_publish.py --test       # 发布到测试PyPI
python build_and_publish.py --prod       # 发布到正式PyPI
python build_and_publish.py --local      # 本地安装测试
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(cmd, check=True):
    """运行命令并显示输出"""
    print(f"运行: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def clean_build():
    """清理构建文件"""
    print("清理构建文件...")
    for pattern in ["build", "dist", "*.egg-info"]:
        run_command(f"rm -rf {pattern}", check=False)


def build_package():
    """构建包"""
    print("构建包...")
    return run_command("python -m build")


def upload_to_test_pypi():
    """上传到测试PyPI"""
    print("上传到测试PyPI...")
    return run_command("python -m twine upload --repository testpypi dist/*")


def upload_to_pypi():
    """上传到正式PyPI"""
    print("上传到PyPI...")
    return run_command("python -m twine upload dist/*")


def install_local():
    """本地安装"""
    print("本地安装...")
    return run_command("pip install -e .")


def check_tools():
    """检查必要的工具"""
    tools = ["build", "twine"]
    missing = []

    for tool in tools:
        result = subprocess.run(
            f"python -m {tool} --help", shell=True, capture_output=True
        )
        if result.returncode != 0:
            missing.append(tool)

    if missing:
        print("缺少构建工具，正在安装...")
        for tool in missing:
            run_command(f"pip install {tool}")


def main():
    parser = argparse.ArgumentParser(description="构建和发布Twitter Space Downloader")
    parser.add_argument("--build", action="store_true", help="只构建包")
    parser.add_argument("--test", action="store_true", help="发布到测试PyPI")
    parser.add_argument("--prod", action="store_true", help="发布到正式PyPI")
    parser.add_argument("--local", action="store_true", help="本地安装")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")

    args = parser.parse_args()

    if not any([args.build, args.test, args.prod, args.local, args.clean]):
        parser.print_help()
        return

    # 检查必要工具
    check_tools()

    # 清理
    if args.clean or any([args.build, args.test, args.prod]):
        clean_build()

    # 构建
    if args.build or args.test or args.prod:
        if not build_package():
            print("构建失败")
            sys.exit(1)
        print("构建成功!")

    # 本地安装
    if args.local:
        if not install_local():
            print("本地安装失败")
            sys.exit(1)
        print("本地安装成功!")

    # 上传到测试PyPI
    if args.test:
        if not upload_to_test_pypi():
            print("上传到测试PyPI失败")
            sys.exit(1)
        print("上传到测试PyPI成功!")
        print("可以使用以下命令测试安装:")
        print("pip install -i https://test.pypi.org/simple/ twitter-space-downloader")

    # 上传到正式PyPI
    if args.prod:
        confirm = input("确定要发布到正式PyPI吗? (y/N): ")
        if confirm.lower() != "y":
            print("取消发布")
            return

        if not upload_to_pypi():
            print("上传到PyPI失败")
            sys.exit(1)
        print("上传到PyPI成功!")
        print("现在用户可以使用以下命令安装:")
        print("pip install twitter-space-downloader")


if __name__ == "__main__":
    main()
