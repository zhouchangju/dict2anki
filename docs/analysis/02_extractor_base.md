# 模块分析: 提取器基类 (extractors/extractor.py)

本模块定义了所有词典提取器必须遵守的“契约” (Contract)，并实现了通用的并发控制和文件输出逻辑。

## 文件信息
*   **路径**: `dict2anki/extractors/extractor.py`
*   **类**: `CardExtractor` (抽象基类)
*   **主要职责**: 定义接口、生成模板、并发调度、写入 CSV。

## 核心类: `CardExtractor`

### 1. 初始化 (`__init__`)
负责设定输出路径和文件名。默认包含：
*   `collection.media` (媒体文件夹)
*   `front-template.txt`, `back-template.txt`, `styling.txt` (Anki 模板)
*   `cards.txt` (核心数据文件)

### 2. 模板生成 (`generate_..._template`)
简单的文件写入操作，将预定义的字符串写入文件。这确保了用户导入 Anki 时有一致的样式。

### 3. 卡片生成核心 (`generate_cards`)
这是本文件的**最复杂**部分，实现了一个基于 `asyncio` 的并发生产线。

**流程图**:

```mermaid
graph TD
    Start[generate_cards called] --> Init[初始化进度条 & 锁]
    Init --> DefineTask[定义内部异步函数 do_get]
    DefineTask --> Gather[asyncio.gather(所有单词)]
    
    subgraph do_get task
        CheckSem{获取信号量?} -->|Yes| RunExec[run_in_executor(self.get_card)]
        RunExec -->|Success| UpdateBar[更新进度条]
        RunExec -->|Fail| LogError[记录错误 & 跳过]
        UpdateBar --> Result[返回字段]
    end
    
    Gather --> Filter[过滤无效结果]
    Filter --> WriteCSV[写入 cards.txt]
    WriteCSV --> End
```

**关键技术点**:
*   **`asyncio.Semaphore(DEFAULT_CONCURRENCY)`**: 限制并发数为 8，防止对目标词典网站造成过大压力或被封禁。
*   **`run_in_executor`**: 因为 `get_card` (具体实现) 包含同步的网络请求 (urllib)，必须在线程池中运行，避免阻塞 Event Loop。
*   **`asyncio.Lock`**: 保护共享资源（如 `visited` 集合、`skipped` 列表、进度条更新），确保线程安全。
*   **去重**: 使用 `visited` 集合防止重复处理相同的单词或重定向后的单词。

### 4. 抽象方法 (`get_card`)
```python
@abstractmethod
def get_card(self, word: str) -> Tuple[str, List[str]]:
    pass
```
*   **输入**: 单词字符串。
*   **输出**: `(实际单词, [正面内容, 背面内容])`。
*   **作用**: 子类必须实现此方法，完成具体的网络请求和 HTML 解析。

## 数据结构
*   **输出格式**: CSV 格式写入，使用 `csv.writer`。这意味着 `cards.txt` 中的字段通过逗号分隔（或根据 dialect 处理），Anki 导入时需注意。

## 异常处理
定义了两个自定义异常：
*   `WordNotFoundError`: 单词未找到。
*   `ExtractError`: 解析过程中出错。
