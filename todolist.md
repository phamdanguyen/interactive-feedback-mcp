# Todolist: interactive-feedback-mcp 二次开发

## 阶段一：UI 现代化与核心体验优化

### 任务 1: UI 布局现代化 (PRD 2.1.1)
*   **描述:** 使用 Qt 布局管理器 (如 `QHBoxLayout`, `QVBoxLayout`) 重新组织 `feedback_ui.py` 中的界面元素，确保窗口缩放时自适应。
*   **具体步骤:**
    *   [ ] 分析 `feedback_ui.py` 中 `_create_ui` 方法的当前布局方式。
    *   [ ] 将 `description_label`, `options_frame` (如果存在), `feedback_text` (自定义的 `FeedbackTextEdit`), 和 `submit_button` 使用 `QVBoxLayout` 和 `QHBoxLayout` 进行合理嵌套布局。
    *   [ ] 移除所有手动设置控件位置和大小的代码 (如 `setGeometry`, `move` 等，除非是顶层窗口的初始设置)。
    *   [ ] 测试窗口缩放，确保所有元素按预期显示和调整。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   UI 元素使用 Qt 布局管理器排列。
    *   窗口缩放时，内部元素自适应。
    *   代码结构清晰，避免手动定位。

### 任务 2: 视觉样式美化 - 基础 (PRD 2.1.2)
*   **描述:** 为应用设定一套基础的 Qt StyleSheets (QSS)，改善整体视觉效果。
*   **具体步骤:**
    *   [ ] 在 `feedback_ui.py` 的 `feedback_ui` 函数或 `FeedbackUI` 初始化中，应用一个简单的全局 QSS。
    *   [ ] 针对 `QPushButton`, `QTextEdit`, `QCheckBox`, `QLabel` 设置基础样式 (如边距、边框、背景色、字体颜色)，以匹配当前已有的暗黑模式 `get_dark_mode_palette` 或提供更统一的外观。
    *   [ ] 确保 `FeedbackTextEdit` 的 `placeholderText` 样式清晰。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   应用统一的视觉风格。
    *   控件具有现代化的基础外观。

### 任务 3: 移除窗口"总在最前"行为 (PRD 2.2.1)
*   **描述:** 修改窗口标志，移除 `Qt.WindowStaysOnTopHint`，使窗口不再强制置顶。
*   **具体步骤:**
    *   [ ] 在 `feedback_ui.py` 的 `FeedbackUI.__init__` 方法中，定位设置 `self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)` 的代码。
    *   [ ] 将其修改为 `self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)` 或确保此标志不被添加。
    *   [ ] 测试窗口行为，确认其不再置顶。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   反馈窗口不再强制置顶。
    *   表现同普通应用窗口。

### 任务 4: 实现点击外部自动最小化 (PRD 2.2.2)
*   **描述:** 当用户点击 UI 页面外部时，反馈窗口自动最小化。
*   **具体步骤:**
    *   [ ] 在 `feedback_ui.py` 的 `FeedbackUI` 类中，重写 `event(self, event)` 方法。
    *   [ ] 在 `event` 方法中，检测 `event.type() == QEvent.WindowDeactivate`。
    *   [ ] 当窗口失活时，如果窗口当前可见且未最小化 (`self.isVisible() and not self.isMinimized()`), 则调用 `self.showMinimized()`。
    *   [ ] 测试在不同应用间切换时，反馈窗口是否按预期自动最小化。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   窗口失活时自动最小化。
    *   避免子对话框激活时错误最小化。

## 阶段二：对话框核心功能增强

### 任务 5: 确保输入后只展示纯文本信息 (PRD 2.3.1)
*   **描述:** 确保从 `FeedbackTextEdit` 获取的是纯文本。
*   **具体步骤:**
    *   [ ] 检查 `feedback_ui.py` 中 `_submit_feedback` 方法。
    *   [ ] 确认 `self.feedback_text.toPlainText().strip()` 已被正确使用来获取反馈文本。
    *   [ ] (如果之前未严格执行) 确保任何从 `predefined_options` 合并的文本也是纯文本。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   使用 `toPlainText()` 获取 `QTextEdit` 内容。
    *   最终反馈信息不含富文本格式。

### 任务 6: 新增回车发送消息功能 (PRD 2.3.3)
*   **描述:** 在 `FeedbackTextEdit` 中，按 Ctrl+Enter (当前已有) 或单独按 Enter 发送消息，Shift+Enter 换行。PRD 要求 Enter 发送，当前是 Ctrl+Enter。需要确认最终行为。**暂定目标：Ctrl+Enter 发送，Enter 换行（保持现有行为，或按需调整为 Enter 发送）。** 此处遵循 `FeedbackTextEdit` 中已有的 `keyPressEvent` 逻辑。如需更改为 Enter 发送，则需修改。
*   **具体步骤 (若维持 Ctrl+Enter):**
    *   [ ] 审阅 `FeedbackTextEdit.keyPressEvent` 方法，确认 Ctrl+Return (即 Ctrl+Enter) 调用 `_submit_feedback`。
    *   [ ] 确认普通 Enter 键行为是换行。
*   **具体步骤 (若改为 Enter 发送, Shift+Enter 换行):**
    *   [ ] 修改 `FeedbackTextEdit.keyPressEvent` 方法。
    *   [ ] 当 `event.key() == Qt.Key_Return` 且 `event.modifiers() == Qt.NoModifier` (或 `not (event.modifiers() & Qt.ShiftModifier)`) 时，调用 `_submit_feedback` 并阻止默认事件。
    *   [ ] 当 `event.key() == Qt.Key_Return` 且 `event.modifiers() == Qt.ShiftModifier` 时，执行默认的换行行为。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准 (根据最终决定调整):**
    *   (Ctrl+Enter): Ctrl+Enter 发送，Enter 换行。
    *   (Enter 发送): Enter 发送，Shift+Enter 换行。

## 阶段三：高级功能实现

### 任务 7: 实现"常用语"功能 - 存储和管理 (PRD 2.4.1)
*   **描述:** 允许用户预设和管理常用的反馈短语，使用 `QSettings` 存储。
*   **具体步骤:**
    *   [x] 创建一个新的 `QDialog` 子类 (例如 `ManageCannedResponsesDialog`) 用于管理常用语。
        *   [x] UI 包含: `QListWidget` 显示常用语, `QLineEdit` 输入/编辑, `QPushButton` (添加, 编辑, 删除, 关闭)。
    *   [x] 实现加载逻辑: 对话框启动时从 `QSettings` (例如组名 `"InteractiveFeedbackMCP/CannedResponses"`, 键名 `"phrases"`) 加载常用语到 `QListWidget`。
    *   [x] 实现添加逻辑: QLineEdit 内容添加到列表和 `QSettings`。
    *   [x] 实现编辑逻辑: 选中列表项内容到 QLineEdit，修改后更新列表和 `QSettings`。
    *   [x] 实现删除逻辑: 从列表和 `QSettings` 中删除选中项。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   提供管理界面支持 CRUD。
    *   `QListWidget` 显示，`QSettings` 存储。

### 任务 8: 实现"常用语"功能 - 访问和使用 (PRD 2.4.2)
*   **描述:** 在主反馈界面提供入口，快速选择并填充常用语。
*   **具体步骤:**
    *   [x] 在 `FeedbackUI._create_ui` 中添加一个 "常用语" `QPushButton`。
    *   [x] 该按钮的 `clicked` 信号连接到一个槽函数，该函数创建并显示 `ManageCannedResponsesDialog` (或一个简化的选择对话框)。
    *   [x] `ManageCannedResponsesDialog` (或选择对话框) 需要一种方式将选中的常用语传递回 `FeedbackUI` (例如通过自定义信号，或在接受对话框后读取选定值)。
    *   [x] `FeedbackUI` 接收到选中的常用语后，将其文本插入到 `self.feedback_text` (例如使用 `insertPlainText()` 或 `setText()`)。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   主界面有"常用语"入口。
    *   点击后显示列表供选择。
    *   选择后自动填充输入框。

## 阶段四：可选高级功能 (根据优先级和时间安排)

### 任务 9: 新增粘贴图片功能 (PRD 2.3.2)
*   **描述:** 允许用户粘贴剪贴板中的图片到反馈对话框并预览。
*   **具体步骤:**
    *   [ ] 在 `FeedbackUI._create_ui` 中添加一个"粘贴图片" `QPushButton` 和一个 `QLabel` 用于图片预览。
    *   [ ] 实现槽函数 `handle_paste_image`:
        *   [ ] 获取 `QApplication.clipboard()`。
        *   [ ] 检查 `mimeData().hasImage()`。
        *   [ ] 若有图片，获取 `clipboard.image()` 并转换为 `QPixmap`。
        *   [ ] 将 `QPixmap` (可缩放以适应 QLabel) 设置到预览 `QLabel`。
    *   [ ] (可选) 考虑通过 `FeedbackTextEdit.keyPressEvent` 或事件过滤器处理 Ctrl+V 快捷键粘贴图片。
    *   **注意:** 此任务仅包含 UI 预览。图片数据如何随反馈发送需进一步设计（PRD 未来考量 6）。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   提供粘贴图片途径。
    *   能检测剪贴板图片。
    *   成功粘贴后 UI 显示预览。

## 阶段五：核心功能 - 实现图片随反馈发送

### 任务 10: 实现图片数据处理与封装 (PRD 2.3.2 扩展)
*   **描述:** 实现将用户粘贴并预览的图片数据进行 Base64 编码，并按照 MCP 服务要求的 JSON 结构进行封装。
*   **具体步骤:**
    *   [ ] 在 `FeedbackUI` 中实现 `get_image_content_data` 方法：
        *   [ ] 从预览 `QLabel` 获取 `QPixmap`。
        *   [ ] 将 `QPixmap` 保存为 PNG 或 JPEG 格式的字节数据。
        *   [ ] 对图片字节数据进行 Base64 编码。
        *   [ ] 返回包含 `type: "image"`, `data: <base64_string>`, `mimeType: "image/png"` (或 "image/jpeg") 的字典。
        *   [ ] 处理图片保存或编码失败的错误情况。
    *   [ ] (可选) 实现客户端图片大小和格式初步校验，超出限制时提示用户。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   能够正确将预览图片转换为 Base64 编码的字符串及对应的 MIME 类型。
    *   输出符合 MCP 服务预期的图片数据结构。
    *   有适当的错误处理。

### 任务 11: 修改反馈提交流程以包含图片 (PRD 2.3.2 扩展)
*   **描述:** 更新 `_submit_feedback` 方法，使其能够同时处理文本反馈和编码后的图片数据，并将它们组合成 MCP 服务要求的最终 JSON 结构。
*   **具体步骤:**
    *   [ ] 修改 `_submit_feedback` 方法：
        *   [ ] 获取纯文本反馈。
        *   [ ] 调用 `get_image_content_data` 获取图片数据字典。
        *   [ ] 构建 `{"content": [...]}` 列表，其中元素可以是文本对象 (如 `{"type": "text", "text": "..."}`) 和图片对象。
        *   [ ] 确保即使没有图片，纯文本反馈也能正常提交。
        *   [ ] 确保即使没有文本，纯图片反馈也能正常提交（如果业务允许）。
    *   [ ] 调整 `FeedbackUI` 的返回值或信号机制，以便调用方能获取到包含图片和文本的完整待提交数据。
    *   [ ] 在提交过程中添加用户反馈（如"正在提交…"）。
    *   [ ] 实现提交失败时的错误提示 (使用 `QMessageBox`)。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   `_submit_feedback` 能正确组装包含文本和/或图片数据的 JSON 结构。
    *   能够将此结构传递给调用 `FeedbackUI` 的代码。
    *   有清晰的提交状态和错误反馈。

### 任务 12: 完善图片粘贴相关的用户体验 (PRD 2.3.2 扩展)
*   **描述:** 增加与图片粘贴和提交流程相关的用户体验优化功能。
*   **具体步骤:**
    *   [ ] 在 `FeedbackUI._create_ui` 中添加一个"清除预览图片" `QPushButton`。
        *   [ ] 该按钮的 `clicked` 信号连接到一个槽函数，用于清除 `QLabel` 中的预览图和已缓存的图片数据。
    *   [ ] (可选) 当预览区域有图片时，提交按钮的文本可以动态更新 (例如，从"提交"变为"提交反馈和图片")。
    *   [ ] (可选) 考虑在 `FeedbackTextEdit` 的 `placeholderText` 中提示可以粘贴图片。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   用户可以清除已粘贴的图片。
    *   UI 交互清晰，符合用户预期。

## 阶段六：优化图片反馈以提升Cursor理解准确性

### 任务 13: 增强图片处理与元数据封装 (对齐参考实现)
*   **描述:** 修改图片处理逻辑和MCP消息结构，以包含更详细的图片元数据，并优化图片尺寸与压缩，旨在提升Cursor对图片内容的理解准确性。
*   **具体步骤:**
    *   [ ] **修改 `feedback_ui.py` 中的 `get_image_content_data` 方法:**
        *   [ ] **调整目标尺寸:** 将 `MAX_IMAGE_WIDTH` 和 `MAX_IMAGE_HEIGHT` 修改为 `512` 像素。
        *   [ ] **调整字节大小限制:** 将 `MAX_IMAGE_BYTES` 调整为 `1048576` (1MB)。
        *   [ ] **优化压缩策略:**
            *   [ ] 默认将图片转换为 JPEG 格式。
            *   [ ] 设置固定的 JPEG 压缩质量 (例如 `80` 或 `85`)。
            *   [ ] (可选，后续优化) 如果固定质量压缩后仍超字节限制，考虑实现逐步降低质量或进一步缩小尺寸的逻辑。
        *   [ ] **收集元数据:** 在图片处理（缩放、压缩）完成后，获取最终图片的宽度、高度、真实的MIME类型 (如 `image/jpeg`, `image/png`) 以及编码为Base64之前的数据字节大小。
        *   [ ] **更新返回值:** 使此方法返回一个包含Base64编码数据、真实MIME类型以及上述收集到的元数据（宽度、高度、字节大小、原始格式等）的字典或对象。

    *   [ ] **修改 `feedback_ui.py` 中的 `_submit_feedback` 方法:**
        *   [ ] **构造新的MCP消息结构:** 当处理每张图片时，在 `content_list` 中为该图片添加两项内容，并确保顺序：
            1.  **元数据文本项 (Text Item for Metadata):**
                *   类型 (type): `"text"`
                *   文本 (text): 一个 JSON 字符串，包含图片处理后的宽度 (width)、高度 (height)、原始格式 (format - 如 'jpeg', 'png')、处理后编码前的字节大小 (size)。例如: `json.dumps({"width": 512, "height": 384, "format": "jpeg", "size": 98765})`。
            2.  **图片数据项 (Image Data Item):**
                *   类型 (type): `"image"`
                *   数据 (data): Base64 编码的图片数据。
                *   MIME类型 (mimeType): 图片数据真实的 MIME 类型 (例如 `"image/jpeg"` 或 `"image/png"`)。
        *   [ ] 确保即使只有文本或只有图片（如果业务允许）也能正确构建 `content_list`。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   图片被缩放到最大 512x512 像素。
    *   图片数据大小被限制在约 1MB 以内。
    *   图片优先被转换为 JPEG 格式并进行压缩。
    *   提交给 MCP 服务的 JSON 数据中，每张图片都包含一个带有其元数据 (宽度, 高度, 格式, 大小) 的文本项，以及一个包含 Base64 数据和真实 MIME 类型的图片项。
    *   元数据文本项在图片数据项之前。
    *   Cursor 对粘贴图片的理解准确性得到显著提升。

---
**最后更新日期:** $(date +%Y-%m-%d) 

## 阶段七：MCP 服务 UI 核心交互优化

### 任务 14: UI 文本可选与复制 (PRD 新增)
*   **描述:** 确保 MCP 服务 UI 窗口内的所有提示文字和选项文字支持鼠标选择和复制。
*   **具体步骤:**
    *   [ ] 调研当前 UI 框架对文本选择的支持程度。
    *   [ ] 识别 `feedback_ui.py` 中所有需要支持文本选择的 `QLabel`、`QPushButton` (按钮文本)、`QCheckBox` (选项文本) 等控件。
    *   [ ] 为目标控件设置相应属性以启用文本选择 (例如，针对 `QLabel` 使用 `setTextInteractionFlags(Qt.TextSelectableByMouse)`).
    *   [ ] 对于按钮等默认文本不可选的控件，考虑是否需要自定义实现或寻找替代方案。
    *   [ ] 测试各区域文本的选择和标准复制操作 (Ctrl+C / 右键菜单)。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   UI 窗口内所有提示性和选项性文字均可通过鼠标选中。
    *   选中的文字可以通过操作系统标准方式复制。

### 任务 15: 输入框支持文件拖拽填充绝对路径 (PRD 新增)
*   **描述:** 允许用户将一个或多个文件拖拽到 UI 的特定输入框 (例如 `FeedbackTextEdit`)，输入框自动填充所有拖拽文件的绝对路径，路径之间用 "; " 分隔。
*   **具体步骤:**
    *   [ ] 在 `FeedbackTextEdit` (或指定的目标输入框) 中启用对拖放事件的接收 (`setAcceptDrops(True)`)。
    *   [ ] 重写 `dragEnterEvent` 方法，检查拖拽数据中是否包含 URL (`event.mimeData().hasUrls()`)，并接受事件。
    *   [ ] 重写 `dragMoveEvent` 方法 (通常简单接受即可)。
    *   [ ] 重写 `dropEvent` 方法:
        *   [ ] 获取 `event.mimeData().urls()`。
        *   [ ] 遍历 URL 列表，对每个 `QUrl`，调用 `toLocalFile()` 获取本地文件绝对路径。
        *   [ ] 将所有获取的绝对路径用 "; " 连接成一个字符串。
        *   [ ] 将拼接后的字符串追加到输入框的当前内容之后 (或替换，根据需求)。
    *   [ ] 测试拖拽单个文件、多个文件，确保路径格式正确。
*   **涉及文件:** `feedback_ui.py`
*   **PRD 验收标准:**
    *   文件可被拖拽到指定输入框。
    *   拖拽后，输入框自动填充一个或多个文件的绝对路径，以 "; " 分隔。
    *   功能稳定，无不当错误。

### 任务 16: 优化图片/文本粘贴后的发送逻辑 (PRD 新增)
*   **描述:** 修正用户在 UI 窗口粘贴内容（图片或文本）后的处理逻辑，确保内容作为一次完整的消息发送给 Cursor。模拟按键序列：ESC -> 等待0.5s -> Ctrl+L -> 等待0.5s -> 注入完整内容 -> 等待0.5s -> Enter。
*   **具体步骤:**
    *   [ ] **核心逻辑定位:** 确定当前处理粘贴后发送消息的函数，可能是 `_submit_feedback` 或 `FeedbackTextEdit.keyPressEvent` 中处理粘贴或特定快捷键的部分。
    *   [ ] **内容捕获增强:** 确保在粘贴事件发生时，能完整捕获剪贴板中的所有内容（例如，如果是富文本编辑器粘贴，能提取出文本和图片标记/数据）。
    *   [ ] **模拟按键序列实现:**
        *   [ ] 需要一个可靠的按键模拟机制 (例如 `QTest.keyClick` 或平台相关的API，如果直接在UI线程中模拟按键给其他应用窗口，则需要更复杂的处理，此处假设是针对 Cursor 自身或其辅助窗口)。
        *   [ ] 在捕获粘贴内容后，按顺序执行：
            1.  模拟 `ESC` 键。
            2.  使用 `QTimer.singleShot(500, ...)` 实现 0.5 秒延迟。
            3.  模拟 `Ctrl+L` 组合键。
            4.  使用 `QTimer.singleShot(500, ...)` 实现 0.5 秒延迟。
            5.  **注入内容:** 将捕获到的完整内容（文本和图片引用/标记）设置到 Cursor 的消息输入区域。*此步骤的具体实现高度依赖于如何与 Cursor 交互。*
            6.  使用 `QTimer.singleShot(500, ...)` 实现 0.5 秒延迟。
            7.  模拟 `Enter` 键。
    *   [ ] **确保原子性:** 整个过程需要设计为能确保用户单次粘贴的所有信息被一次性完整发送。
    *   [ ] **测试:** 详细测试纯文本粘贴、纯图片粘贴、图文混合粘贴，验证消息的完整性和发送时序。
*   **涉及文件:** `feedback_ui.py` (主要), 可能涉及与 Cursor 交互的模块。
*   **PRD 验收标准:**
    *   粘贴操作后，定义的按键序列被正确执行。
    *   用户在 UI 窗口粘贴的图片和文字被完整地作为一次对话发送给 Cursor。
    *   解决了之前内容可能被分割发送的问题。 