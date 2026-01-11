# 模块分析: 工具与日志 (utils.py)

本模块提供了项目通用的基础设施，包括日志记录、文件路径清洗和命令行进度条。

## 文件信息
*   **路径**: `dict2anki/utils.py`
*   **主要职责**: 统一日志格式、跨平台路径处理、可视化进度反馈。

## 核心组件

### 1. `Log` 类
一个静态工具类，模拟了 Android 开发中常见的 Log 风格 (`Log.d`, `Log.i`, `Log.e`)。

*   **ANSI 颜色支持**: 检测 `TERM` 环境变量。如果是 `xterm`, `linux` 等终端，会自动为不同级别的日志添加颜色（Error 为红，Info 为绿等）。
*   **级别控制**: 通过 `Log.level` 静态变量控制输出详细程度 (DEBUG/INFO/WARN/ERROR)。
*   **输出目标**: 所有日志默认输出到 `sys.stderr`，不干扰 `sys.stdout` 的管道输出。

### 2. `valid_path(path, force=True)`
确保文件路径合法且不冲突。
*   **目录创建**: 如果父目录不存在，自动创建。
*   **字符清洗**: 将文件名中的非法字符 (`/:*?"<>|`) 替换为下划线 `_`。
*   **重名处理 (`force=False`)**: 如果文件已存在且 `force` 为 False，它会自动在文件名后追加 `_(1)`, `_(2)` 等数字后缀，避免覆盖。这在下载同名资源时非常有用。

### 3. `ProgressBar` 类
一个手动实现的命令行进度条。

*   **样式**: ` 25.0% ├██████───────────────────┤ word / total`
*   **原理**: 使用 `sys.stdout.write('\r' + line)` 回车符将光标移回行首，实现原地刷新。
*   **属性**: 支持动态设置 `total` (总数), `progress` (当前进度), `extra` (额外信息，如当前处理的单词)。

## 代码示例 (ProgressBar)

```python
bar = ProgressBar(100)
for i in range(100):
    # do something
    bar.increment()
bar.done()
```

## 评价
`utils.py` 展示了作者即使在构建简单的 CLI 工具时也注重用户体验（彩色日志、进度条）。`valid_path` 是一个非常实用的函数，值得保留。`Log` 类虽然简单，但在多线程/多进程环境下可能存在竞态条件（虽然 `sys.stderr.write` 通常是原子操作，但多个 `write` 调用组合则不是），但在当前的 `asyncio` 单线程并发模型下是安全的。
