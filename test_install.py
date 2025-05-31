#!/usr/bin/env python3
"""
测试安装脚本
用于验证包是否可以正常安装和导入
"""

import subprocess
import sys


def test_import():
    """测试是否可以导入模块"""
    try:
        from twitter_space_downloader import TwitterSpaceDownloader

        print("✅ 模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_cli():
    """测试命令行工具是否可用"""
    try:
        result = subprocess.run(
            ["twitter-space-downloader", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("✅ 命令行工具可用")
            return True
        else:
            print(f"❌ 命令行工具错误: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ 命令行工具未找到")
        return False
    except subprocess.TimeoutExpired:
        print("❌ 命令行工具超时")
        return False


def test_short_cli():
    """测试简短命令别名"""
    try:
        result = subprocess.run(
            ["tsd", "--help"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ 简短命令别名可用")
            return True
        else:
            print(f"❌ 简短命令别名错误: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ 简短命令别名未找到")
        return False
    except subprocess.TimeoutExpired:
        print("❌ 简短命令别名超时")
        return False


def main():
    print("🧪 开始测试安装...")
    print("=" * 50)

    tests = [
        ("模块导入测试", test_import),
        ("命令行工具测试", test_cli),
        ("简短命令测试", test_short_cli),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}:")
        result = test_func()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 测试结果:")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 所有测试通过 ({passed}/{total})")
        print("✅ 包安装成功，可以正常使用！")
    else:
        print(f"⚠️  部分测试失败 ({passed}/{total})")
        print("❌ 请检查安装或环境配置")
        sys.exit(1)


if __name__ == "__main__":
    main()
