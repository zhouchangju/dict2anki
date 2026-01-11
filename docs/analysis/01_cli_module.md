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
    parse_args() # 1. 解析参数
    
    # 2. 设置网络超时
    socket.setdefaulttimeout(DEFAULT_TIME_OUT)

    # 3. 实例化提取器 (工厂模式)
    # EXTRACTORS 是一个字典，映射名称到类
    e = EXTRACTORS[extractor](output_path)
    
    # 4. 生成 Anki 必要的模板文件
    e.generate_front_template()
    e.generate_back_template()
    e.generate_styling()
    
    # 5. 开始批量生成卡片
    # *words 解包列表作为参数传递
    e.generate_cards(*words)
```

### 4. 输入处理
在 `parse_args` 中包含了一段读取输入文件的逻辑：
*   按行读取。
*   去除首尾空格。
*   忽略空行。
*   **忽略以 `#` 开头的注释行**。

## 依赖关系
*   **Imports**: `argparse`, `os`, `socket`, `sys`
*   **Internal**: `extractors` (获取提取器列表), `utils` (日志)

## 改进建议 (用于重写)
*   目前 `words` 加载逻辑耦合在 `parse_args` 中，建议分离为独立的 `load_words` 函数。
*   全局变量 (`extractor`, `output_path`, `words`) 使用较多，建议封装进一个 `Config` 对象或 `Context` 类传递。
