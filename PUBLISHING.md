# 发布说明

本文档说明如何构建和发布 Twitter Space Downloader 包。

## 前置条件

1. **PyPI账户**: 需要在 [PyPI](https://pypi.org/) 和 [TestPyPI](https://test.pypi.org/) 注册账户
2. **API令牌**: 配置PyPI API令牌（推荐使用令牌而非密码）
3. **ffmpeg**: 确保系统安装了ffmpeg

## 快速发布

我们提供了自动化脚本来简化发布过程：

### 1. 本地测试安装

```bash
# 本地开发模式安装
python build_and_publish.py --local

# 运行测试验证
python test_install.py
```

### 2. 发布到测试PyPI

```bash
# 构建并发布到测试PyPI
python build_and_publish.py --test

# 从测试PyPI安装验证
pip install -i https://test.pypi.org/simple/ twitter-space-downloader
```

### 3. 发布到正式PyPI

```bash
# 发布到正式PyPI（需要确认）
python build_and_publish.py --prod
```

## 手动发布流程

如果需要手动控制发布过程：

### 1. 准备环境

```bash
# 安装构建工具
pip install build twine

# 清理旧文件
rm -rf build/ dist/ *.egg-info/
```

### 2. 构建包

```bash
# 构建源码包和wheel包
python -m build
```

这会在 `dist/` 目录下生成：
- `twitter-space-downloader-1.0.0.tar.gz` (源码包)
- `twitter_space_downloader-1.0.0-py3-none-any.whl` (wheel包)

### 3. 检查包

```bash
# 检查包的元数据
python -m twine check dist/*
```

### 4. 发布到测试PyPI

```bash
# 上传到测试PyPI
python -m twine upload --repository testpypi dist/*

# 从测试PyPI安装
pip install -i https://test.pypi.org/simple/ twitter-space-downloader
```

### 5. 发布到正式PyPI

```bash
# 上传到正式PyPI
python -m twine upload dist/*
```

## API令牌配置

### 创建令牌

1. 登录 [PyPI](https://pypi.org/manage/account/)
2. 进入 Account settings → API tokens
3. 创建新令牌，选择范围为特定项目或所有项目

### 配置令牌

#### 方式1: 使用 .pypirc 文件

创建 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

#### 方式2: 命令行传入

```bash
# 发布时输入用户名：__token__，密码：你的令牌
python -m twine upload dist/*
```

## 版本管理

### 更新版本号

需要同时更新以下文件中的版本号：
- `pyproject.toml` 中的 `version`
- `twitter_space_downloader/__init__.py` 中的 `__version__`

### 版本号约定

使用语义化版本号 (SemVer)：
- `1.0.0` - 主版本号
- `1.1.0` - 次版本号（新功能）
- `1.0.1` - 修订号（bug修复）

## 发布检查清单

发布前确认：

- [ ] 更新版本号
- [ ] 更新 CHANGELOG.md
- [ ] 运行所有测试
- [ ] 更新 README.md
- [ ] 清理临时文件
- [ ] 检查依赖版本
- [ ] 本地测试安装
- [ ] 测试PyPI发布验证
- [ ] 正式PyPI发布

## 故障排除

### 常见问题

1. **权限错误**: 检查API令牌是否正确配置
2. **版本冲突**: 确保新版本号未被使用
3. **依赖问题**: 检查requirements.txt中的版本约束
4. **构建失败**: 检查pyproject.toml配置

### 重新发布

如果需要修复已发布的版本：

1. 修复问题
2. 增加版本号（例如：1.0.0 → 1.0.1）
3. 重新构建和发布

注意：PyPI不允许重新上传相同版本号的包。

## 命令行工具验证

发布后验证命令行工具：

```bash
# 全局安装
pip install twitter-space-downloader

# 测试命令
twitter-space-downloader --help
tsd --help

# 测试完整功能（需要真实URL）
# twitter-space-downloader "https://twitter.com/i/spaces/1234567890"
```

## 自动化CI/CD

可以配置GitHub Actions等CI/CD工具实现自动化发布：

1. 在仓库secrets中配置PyPI令牌
2. 创建发布工作流
3. 推送标签时自动发布

这样可以确保每次发布都经过完整的测试流程。 