# 模块分析: CLI 与入口 (cli.py & \_\_main\_\_.py)

本模块是程序的“点火钥匙”，负责接收用户指令并启动程序。

## 文件信息
*   **路径**: `dict2anki/cli.py`, `dict2anki/__main__.py`
*   **主要职责**: 参数解析、环境初始化、提取器选择、输入读取。

## 详细功能实现

### 1. 入口 (`__main__.py`)
极其简单，仅作为包的执行入口，调用 `cli.main()`。

```python
from .cli import main
if __name__ == '__main__':
    main()
```

### 2. 参数解析 (`parse_args`)
使用 Python 标准库 `argparse` 定义并解析以下参数：

| 参数 | 缩写 | 描述 | 默认值 |
| :--- | :--- | :--- | :--- |
| `--input-file` | `-i` | 输入的单词文件路径 (必须) | None |
| `--output-path` | `-o` | 输出目录路径 | 当前目录 |
| `--extractor` | `-e` | 选择使用的词典引擎 | cambridge |
| `--debug` | `-d` | 开启调试日志 | False |

**关键逻辑**:
*   若未提供 `-i`，打印帮助并退出。
*   检查 `-e` 指定的提取器是否存在于 `EXTRACTORS` 注册表中。
*   设置全局日志级别 (`Log.level`)。

### 3. 主流程 (`main`)
这是整个程序的编排中心。

```python
def main():
    # 1. 解析参数，返回配置和数据，不依赖全局变量
    extractor_name, output_path, words = parse_args()
    
    # 2. 设置网络超时
    socket.setdefaulttimeout(DEFAULT_TIME_OUT)

    # 3. 实例化提取器 (工厂模式)
    extractor_class = EXTRACTORS[extractor_name]
    extractor = extractor_class(output_path)
    
    # 4. 生成 Anki 必要的模板文件
    extractor.generate_front_template()
    extractor.generate_back_template()
    extractor.generate_styling()
    
    # 5. 开始批量生成卡片
    extractor.generate_cards(*words)
```

### 4. 输入处理
在 `parse_args` 中包含了一段读取输入文件的逻辑：
*   按行读取。
*   去除首尾空格。
*   忽略空行。
*   **忽略以 `#` 开头的注释行**。
*   使用上下文管理器 (`with`) 安全打开和关闭文件。

## 依赖关系
*   **Imports**: `argparse`, `os`, `socket`, `typing`
*   **Internal**: `extractors` (获取提取器列表), `utils` (日志)

## 改进建议 (已实施)
*   `words` 加载逻辑集成在 `parse_args` 中，并返回给 `main`。
*   全局变量 (`extractor`, `output_path`, `words`) 已被移除，改为通过函数返回值传递。
