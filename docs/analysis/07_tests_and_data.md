# 模块分析: 测试与数据格式 (Tests & Data)

本模块分析项目的测试策略以及核心数据文件的格式。

## 测试策略 (`tests/`)

项目使用 Python 标准库 `unittest` 框架。

### `tests/test_extractor_cambridge.py`
这是一个**集成测试**，而非单纯的单元测试，因为它依赖真实的互联网连接。

```python
class TestCambridge(TestCase):
    def test_CambridgeExtractor(self):
        extractor = CambridgeExtractor()
        # 1. 验证重定向逻辑 (cater to -> cater for sb sth)
        self.assertEqual('cater for sb sth', extractor.get_card('cater to')[0])
        
        # 2. 验证格式化 (去除多余空格)
        self.assertEqual('cater for sb sth', extractor.get_card('  cater   for sb/sth ')[0])
        
        # 3. 验证完整流程 (生成模板与卡片)
        extractor.generate_front_template()
        extractor.generate_back_template()
        extractor.generate_styling()
        words = ('list', 'chat', 'abbreviate')
        extractor.generate_cards(*words)
```

**风险**: 这种测试极不稳定。如果剑桥词典网站挂了，或者该单词的释义发生了微调，测试就会失败。CI/CD 环境中应谨慎运行此类测试，或使用 Mock/VCR 录制。

## 数据格式分析

### 1. 输入: `words.txt`
*   纯文本文件。
*   分隔符: 换行符 `\n`。
*   注释: `#` 开头的行。
*   示例:
    ```text
abandon
# 这是一个注释
world
```

### 2. 输出: `cards.txt`
*   **格式**: CSV (无表头)。
*   **列结构**: `[正面, 背面]`。
*   **正面**: 通常是单词本身，或者是包含 HTML 的简单结构 `<div style="text-align:center">word</div>`。
*   **背面**: 复杂的 HTML 片段，包含定义、音标、例句等，已经过清洗和格式化。

### 3. Anki 模板文件
为了让导入的卡片在 Anki 中显示正常，工具生成了以下文件：

| 文件 | 作用 | 内容特征 |
| :--- | :--- | :--- |
| `front-template.txt` | 正面模板 | `{{正面}}` |
| `back-template.txt` | 背面模板 | `{{FrontSide}}<hr id=answer>{{背面}}` |
| `styling.txt` | CSS 样式 | 包含 `.card` 样式，以及内嵌的 `<script>` (AMP JS) |

## 总结
当前的测试覆盖了“快乐路径”（Happy Path），即一切正常的情况。缺乏对网络超时、解析错误、特殊字符（如 emoji 或生僻字）的边缘情况测试。数据格式简单直接，紧密贴合 Anki 的导入需求。

```