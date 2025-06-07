# 可拖拽分隔器实现计划

## 项目概述
为 interactive-feedback MCP 服务添加可拖拽分隔器功能，允许用户通过拖拽分割线来动态调整提示文字区域和输入框区域的大小比例。

## 技术方案
使用 Qt 的 QSplitter 组件实现，该方案具有以下优势：
- Qt 原生支持，稳定可靠
- 用户体验良好，支持平滑拖拽
- 自动处理鼠标事件和视觉反馈
- 易于样式定制和状态保存

## 详细实施任务

### 任务 1：常量定义扩展
**文件**: `src/feedback_ui/utils/constants.py`
**目标**: 添加分割器相关的常量定义

**具体操作**:
```python
# 分割器设置相关常量
SETTINGS_KEY_SPLITTER_SIZES = "splitterSizes"
SETTINGS_KEY_SPLITTER_STATE = "splitterState"

# 默认区域高度（像素）
DEFAULT_UPPER_AREA_HEIGHT = 250
DEFAULT_LOWER_AREA_HEIGHT = 400
DEFAULT_SPLITTER_RATIO = [250, 400]  # 上:下 = 250:400

# 最小区域高度限制
MIN_UPPER_AREA_HEIGHT = 150
MIN_LOWER_AREA_HEIGHT = 200
```

### 任务 2：设置管理器扩展
**文件**: `src/feedback_ui/utils/settings_manager.py`
**目标**: 添加分割器状态的保存和恢复功能

**具体操作**:
1. 导入新增的常量
2. 添加以下方法：

```python
def get_splitter_sizes(self) -> list[int]:
    """获取保存的分割器尺寸比例"""
    self.settings.beginGroup(SETTINGS_GROUP_MAIN)
    sizes = self.settings.value(SETTINGS_KEY_SPLITTER_SIZES, DEFAULT_SPLITTER_RATIO)
    self.settings.endGroup()
    
    # 确保返回有效的整数列表
    if isinstance(sizes, list) and len(sizes) == 2:
        try:
            return [int(sizes[0]), int(sizes[1])]
        except (ValueError, TypeError):
            return DEFAULT_SPLITTER_RATIO
    return DEFAULT_SPLITTER_RATIO

def set_splitter_sizes(self, sizes: list[int]):
    """保存分割器尺寸比例"""
    if len(sizes) == 2:
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_SPLITTER_SIZES, sizes)
        self.settings.endGroup()
        self.settings.sync()

def get_splitter_state(self) -> bytes | None:
    """获取分割器状态"""
    self.settings.beginGroup(SETTINGS_GROUP_MAIN)
    state = self.settings.value(SETTINGS_KEY_SPLITTER_STATE, None)
    self.settings.endGroup()
    return state if isinstance(state, (bytes, type(None))) else None

def set_splitter_state(self, state: bytes):
    """保存分割器状态"""
    self.settings.beginGroup(SETTINGS_GROUP_MAIN)
    self.settings.setValue(SETTINGS_KEY_SPLITTER_STATE, state)
    self.settings.endGroup()
    self.settings.sync()
```

### 任务 3：主窗口布局重构
**文件**: `src/feedback_ui/main_window.py`
**目标**: 将现有布局改为使用 QSplitter

**具体操作**:

#### 3.1 添加导入
```python
from PySide6.QtWidgets import QSplitter
```

#### 3.2 修改 `_create_ui_layout` 方法
将现有的垂直布局结构改为分割器结构：

```python
def _create_ui_layout(self):
    """Creates the main UI layout with splitter for resizable areas."""
    central_widget = QWidget()
    self.setCentralWidget(central_widget)

    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(20, 5, 20, 10)
    main_layout.setSpacing(15)

    # 创建主分割器
    self.main_splitter = QSplitter(Qt.Orientation.Vertical)
    self.main_splitter.setObjectName("mainSplitter")
    
    # 创建上部区域（提示文字 + 选项）
    self.upper_area = self._create_upper_area()
    self.main_splitter.addWidget(self.upper_area)
    
    # 创建下部区域（输入框）
    self.lower_area = self._create_lower_area()
    self.main_splitter.addWidget(self.lower_area)
    
    # 配置分割器属性
    self._setup_splitter_properties()
    
    main_layout.addWidget(self.main_splitter)
    self._setup_bottom_bar(main_layout)
    
    # 提交按钮
    current_language = self.settings_manager.get_current_language()
    self.submit_button = QPushButton(
        self.button_texts["submit_button"][current_language]
    )
    self.submit_button.setObjectName("submit_button")
    self.submit_button.setMinimumHeight(50)
    main_layout.addWidget(self.submit_button)

    self._create_github_link_area(main_layout)
    self._update_submit_button_text_status()
```

#### 3.3 添加新方法
```python
def _create_upper_area(self) -> QWidget:
    """创建上部区域容器（提示文字 + 选项）"""
    upper_widget = QWidget()
    upper_layout = QVBoxLayout(upper_widget)
    upper_layout.setContentsMargins(15, 5, 15, 15)
    upper_layout.setSpacing(10)
    
    # 添加现有的描述区域
    self._create_description_area(upper_layout)
    
    # 添加选项复选框（如果有）
    if self.predefined_options:
        self._create_options_checkboxes(upper_layout)
    
    return upper_widget

def _create_lower_area(self) -> QWidget:
    """创建下部区域容器（输入框）"""
    lower_widget = QWidget()
    lower_layout = QVBoxLayout(lower_widget)
    lower_layout.setContentsMargins(15, 5, 15, 15)
    lower_layout.setSpacing(10)
    
    # 添加输入提交区域
    self._create_input_submission_area(lower_layout)
    
    return lower_widget

def _setup_splitter_properties(self):
    """配置分割器属性"""
    # 设置分割器手柄宽度
    self.main_splitter.setHandleWidth(8)
    
    # 设置最小尺寸
    self.upper_area.setMinimumHeight(MIN_UPPER_AREA_HEIGHT)
    self.lower_area.setMinimumHeight(MIN_LOWER_AREA_HEIGHT)
    
    # 设置初始尺寸
    saved_sizes = self.settings_manager.get_splitter_sizes()
    self.main_splitter.setSizes(saved_sizes)
    
    # 连接信号以保存状态
    self.main_splitter.splitterMoved.connect(self._on_splitter_moved)
    
    # 恢复分割器状态
    saved_state = self.settings_manager.get_splitter_state()
    if saved_state:
        self.main_splitter.restoreState(saved_state)

def _on_splitter_moved(self, pos: int, index: int):
    """分割器移动时保存状态"""
    sizes = self.main_splitter.sizes()
    self.settings_manager.set_splitter_sizes(sizes)
    self.settings_manager.set_splitter_state(self.main_splitter.saveState())
```

### 任务 4：样式文件更新
**文件**: `src/feedback_ui/styles/dark_theme.qss` 和 `src/feedback_ui/styles/light_theme.qss`
**目标**: 为分割器添加美观的样式

**深色主题样式**:
```css
/* QSplitter 样式 */
QSplitter {
    background-color: #2b2b2b;
}

QSplitter::handle {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 2px;
    margin: 2px;
}

QSplitter::handle:horizontal {
    width: 8px;
    min-width: 8px;
}

QSplitter::handle:vertical {
    height: 8px;
    min-height: 8px;
}

QSplitter::handle:hover {
    background-color: #505050;
    border-color: #666666;
}

QSplitter::handle:pressed {
    background-color: #606060;
}

/* 分割器手柄中间的装饰线 */
QSplitter::handle:vertical {
    background-image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iNCIgdmlld0JveD0iMCAwIDIwIDQiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMCIgaGVpZ2h0PSIxIiBmaWxsPSIjNzc3Nzc3Ii8+CjxyZWN0IHk9IjMiIHdpZHRoPSIyMCIgaGVpZ2h0PSIxIiBmaWxsPSIjNzc3Nzc3Ii8+Cjwvc3ZnPgo=);
    background-repeat: no-repeat;
    background-position: center;
}
```

**浅色主题样式**:
```css
/* QSplitter 样式 */
QSplitter {
    background-color: #f5f5f5;
}

QSplitter::handle {
    background-color: #e0e0e0;
    border: 1px solid #cccccc;
    border-radius: 2px;
    margin: 2px;
}

QSplitter::handle:hover {
    background-color: #d0d0d0;
    border-color: #bbbbbb;
}

QSplitter::handle:pressed {
    background-color: #c0c0c0;
}

QSplitter::handle:vertical {
    background-image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iNCIgdmlld0JveD0iMCAwIDIwIDQiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMCIgaGVpZ2h0PSIxIiBmaWxsPSIjOTk5OTk5Ii8+CjxyZWN0IHk9IjMiIHdpZHRoPSIyMCIgaGVpZ2h0PSIxIiBmaWxsPSIjOTk5OTk5Ii8+Cjwvc3ZnPgo=);
    background-repeat: no-repeat;
    background-position: center;
}
```

### 任务 5：增强功能实现
**目标**: 添加用户体验优化功能

#### 5.1 双击重置功能
在主窗口中添加：
```python
def _setup_splitter_properties(self):
    # ... 现有代码 ...
    
    # 双击重置功能
    self.main_splitter.handle(1).mouseDoubleClickEvent = self._reset_splitter_to_default

def _reset_splitter_to_default(self, event):
    """双击分割器手柄时重置为默认比例"""
    self.main_splitter.setSizes(DEFAULT_SPLITTER_RATIO)
    self._on_splitter_moved(0, 0)  # 保存新的状态
```

#### 5.2 键盘快捷键支持（可选）
```python
def keyPressEvent(self, event):
    """处理键盘快捷键"""
    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        if event.key() == Qt.Key.Key_Equal:  # Ctrl + =
            # 增加上部区域
            sizes = self.main_splitter.sizes()
            sizes[0] += 20
            sizes[1] -= 20
            if sizes[1] >= MIN_LOWER_AREA_HEIGHT:
                self.main_splitter.setSizes(sizes)
                self._on_splitter_moved(0, 0)
            return
        elif event.key() == Qt.Key.Key_Minus:  # Ctrl + -
            # 减少上部区域
            sizes = self.main_splitter.sizes()
            sizes[0] -= 20
            sizes[1] += 20
            if sizes[0] >= MIN_UPPER_AREA_HEIGHT:
                self.main_splitter.setSizes(sizes)
                self._on_splitter_moved(0, 0)
            return
    
    super().keyPressEvent(event)
```

## 测试验证

### 功能测试
1. **基本拖拽**: 验证可以通过拖拽调整区域大小
2. **比例保存**: 验证关闭重开后比例得到保持
3. **最小尺寸**: 验证不能拖拽到过小尺寸
4. **双击重置**: 验证双击可以恢复默认比例
5. **样式显示**: 验证分割器外观符合主题

### 兼容性测试
1. **现有功能**: 确保不影响其他已有功能
2. **响应式**: 验证窗口缩放时分割器正常工作
3. **主题切换**: 验证深色/浅色主题下样式正确

## 预期效果
- 用户可以自由调整提示区域和输入区域的大小比例
- 调整后的比例会自动保存并在下次启动时恢复
- 分割器外观美观，与整体UI风格一致
- 提供双击重置和键盘快捷键等便利功能
- 不影响现有的任何功能

## 实施优先级
1. **P0 (必须)**: 任务1-3，实现基本的分割器功能
2. **P1 (重要)**: 任务4，样式美化
3. **P2 (可选)**: 任务5，增强功能

## 风险评估
- **低风险**: 使用Qt原生组件，稳定性有保障
- **向后兼容**: 不会破坏现有功能
- **回滚方案**: 如有问题可以快速回退到原有布局

## 实施检查清单

### 开发阶段
- [ ] 任务1: 添加常量定义
- [ ] 任务2: 扩展设置管理器
- [ ] 任务3.1: 修改主窗口导入
- [ ] 任务3.2: 重构 `_create_ui_layout` 方法
- [ ] 任务3.3: 添加新的辅助方法
- [ ] 任务4: 更新样式文件
- [ ] 任务5: 实现增强功能

### 测试阶段
- [ ] 基本拖拽功能测试
- [ ] 比例保存和恢复测试
- [ ] 最小尺寸限制测试
- [ ] 双击重置功能测试
- [ ] 样式在不同主题下的显示测试
- [ ] 现有功能兼容性测试
- [ ] 窗口缩放响应式测试

### 部署阶段
- [ ] 代码审查
- [ ] 性能测试
- [ ] 用户体验测试
- [ ] 文档更新

## 代码示例补充

### 完整的 `_create_ui_layout` 方法实现
```python
def _create_ui_layout(self):
    """Creates the main UI layout with splitter for resizable areas."""
    central_widget = QWidget()
    self.setCentralWidget(central_widget)

    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(20, 5, 20, 10)
    main_layout.setSpacing(15)

    # 创建主分割器
    self.main_splitter = QSplitter(Qt.Orientation.Vertical)
    self.main_splitter.setObjectName("mainSplitter")
    self.main_splitter.setChildrenCollapsible(False)  # 防止区域被完全折叠

    # 创建上部区域（提示文字 + 选项）
    self.upper_area = self._create_upper_area()
    self.main_splitter.addWidget(self.upper_area)

    # 创建下部区域（输入框）
    self.lower_area = self._create_lower_area()
    self.main_splitter.addWidget(self.lower_area)

    # 配置分割器属性
    self._setup_splitter_properties()

    main_layout.addWidget(self.main_splitter)
    self._setup_bottom_bar(main_layout)

    # 提交按钮
    current_language = self.settings_manager.get_current_language()
    self.submit_button = QPushButton(
        self.button_texts["submit_button"][current_language]
    )
    self.submit_button.setObjectName("submit_button")
    self.submit_button.setMinimumHeight(50)
    main_layout.addWidget(self.submit_button)

    self._create_github_link_area(main_layout)
    self._update_submit_button_text_status()
```

### 窗口关闭时保存状态
```python
def closeEvent(self, event):
    """窗口关闭时保存所有状态"""
    # 保存分割器状态
    if hasattr(self, 'main_splitter'):
        sizes = self.main_splitter.sizes()
        self.settings_manager.set_splitter_sizes(sizes)
        self.settings_manager.set_splitter_state(self.main_splitter.saveState())

    # 保存窗口几何信息
    self.settings_manager.set_main_window_geometry(self.saveGeometry())
    self.settings_manager.set_main_window_state(self.saveState())
    self.settings_manager.set_main_window_size(self.width(), self.height())
    self.settings_manager.set_main_window_position(self.x(), self.y())

    super().closeEvent(event)
```

## 注意事项

### 布局迁移要点
1. **保持现有组件**: 不改变现有的 `_create_description_area` 和 `_create_input_submission_area` 方法
2. **分离关注点**: 上下区域分别封装在独立的容器中
3. **信号连接**: 确保所有现有的信号连接保持不变
4. **样式继承**: 新容器应该继承现有的样式设置

### 性能考虑
1. **避免频繁保存**: 使用定时器延迟保存，避免拖拽时频繁写入设置
2. **内存管理**: 确保分割器和容器的正确内存管理
3. **响应性**: 保持UI的响应性，避免阻塞主线程

### 用户体验
1. **直观操作**: 分割器手柄应该有明显的视觉提示
2. **合理限制**: 设置合理的最小尺寸，防止区域过小影响使用
3. **状态恢复**: 确保用户的调整在重启后得到保持

## 后续优化建议

### 可能的增强功能
1. **预设比例**: 提供几个预设的比例选项（如 1:1, 1:2, 2:1）
2. **动画效果**: 添加平滑的调整动画
3. **触摸支持**: 为触摸设备优化分割器操作
4. **快捷菜单**: 右键分割器显示快捷操作菜单

### 可访问性改进
1. **键盘导航**: 支持Tab键导航到分割器
2. **屏幕阅读器**: 为分割器添加适当的可访问性标签
3. **高对比度**: 在高对比度模式下提供更明显的视觉提示

这个实施计划提供了完整的技术路线图，可以按照优先级逐步实现，确保功能的稳定性和用户体验的优化。
