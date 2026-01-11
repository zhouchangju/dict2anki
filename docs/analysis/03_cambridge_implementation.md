# 模块分析: 剑桥词典实现 (extractors/cambridge.py)

本模块是 `CardExtractor` 的具体实现，负责处理剑桥词典 (Cambridge Dictionary) 的页面逻辑。

## 文件信息
*   **路径**: `dict2anki/extractors/cambridge.py`
*   **类**: `CambridgeExtractor`
*   **主要职责**: 获取 CSS/Font，下载单词页面，清洗 HTML，提取定义。

## 关键常量

*   `URL_ROOT`, `URL_QUERY`: 定义了词典的基础地址和查询接口。
*   `URL_STYLE`, `URL_FONT`: 用于获取词典的原始 CSS 和字体文件，以保持原汁原味的显示效果。
*   `THRESHOLD_COLLAPSE`: 4096 字节。如果 HTML 内容过长，会触发折叠逻辑 (`_collapse`)，使用 AMP (Accelerated Mobile Pages) 组件。

## 核心方法实现

### 1. `_retrieve_styling`
此方法不仅仅是下载 CSS，还做了**本地化处理**：
1.  下载 `common.css`。
2.  下载字体文件 `cdoicons.woff` 并重命名为 `_cdoicons.woff` (Anki 规范：下划线开头的文件在媒体库中)。
3.  **正则替换**: 将 CSS 中引用的远程字体 URL 替换为本地文件名。
4.  **注入自定义样式**: 添加 `.large-ipa` 类，设置字体大小为 24px，颜色为深灰，用于突出显示音标。
5.  注入 AMP 相关的 JS 脚本引用（用于折叠效果）。

### 2. `get_card(self, word)`
实现了基类的抽象方法。
1.  **构建 URL**: 将单词 URL 编码后拼接到查询 URL。
2.  **网络请求**: 调用 `urlopen_with_retry`。
3.  **处理重定向**: 检测 URL 变化，获取单词的“真实拼写”（例如搜 "colour" 重定向到 "color"）。
4.  **调用提取**: `_extract_fields(content)`。
5.  **返回**: 真实单词和 `[Front, Back]` 列表。

### 3. `_extract_fields(self, html_str)` (最核心逻辑)
负责将原始 HTML 转化为干净的卡片内容。大量使用了 `htmls.py` 的工具函数。

**清洗步骤 (Pipeline)**:
1.  **定位**: 找到 `div class="di-body"` (主体) 和 `div class="di-title"` (标题/正面)。
2.  **正面增强 (New)**:
    *   **提取音标**: 查找 `span class="ipa"`，将其包裹在 `<div class="large-ipa">` 中添加到正面。
    *   **提取音频**: 扫描所有 `/zhs/media` 开头的音频链接。**优先匹配包含 `us_pron` (美音) 的链接**，若未找到则使用第一个。生成 `<audio autoplay controls>` 标签添加到正面，实现自动播放。
3.  **移除杂项**:
    *   移除标题 (避免背面重复)。
    *   移除 `xref` (交叉引用/习语跳转)。
    *   移除 `share` (分享按钮)。
    *   移除 `script` 标签。
    *   移除广告 (`ad_contentslot`).
4.  **修正链接**:
    *   移除 `<a>` 标签但保留内容（防止在 Anki 中误触跳转）。
    *   **音频修复**: 将相对路径 `/zhs/media` 替换为绝对路径，使其能在线播放 (注意：本项目默认不下载音频文件，而是使用在线链接)。
5.  **折叠处理**: 如果内容太长，调用 `_collapse` 将解释块包裹在 `<amp-accordion>` 中。

### 4. `_collapse`
针对长条目进行优化。使用正则和字符串替换，将原本的定义块 (`def-block`) 转换为可折叠的 AMP 组件结构。

## 依赖关系
*   **External**: 无第三方库。
*   **Internal**:
    *   `dict2anki.net`: 处理 HTTP。
    *   `dict2anki.htmls`: 处理 HTML 标签查找和替换。

## 观察与潜在问题
*   **脆弱性**: 严重依赖剑桥词典的 HTML 类名 (如 `di-body`, `di-title`, `daccord`). 如果网站改版，此提取器将立即失效。
*   **AMP 依赖**: 使用了 Google AMP 组件来实现折叠，这意味着生成的卡片需要在支持 JS/AMP 的 Anki 客户端上才能完美显示。
