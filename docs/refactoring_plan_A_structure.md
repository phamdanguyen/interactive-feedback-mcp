# 优化方案A: 项目结构与打包 (Project Structure & Packaging Plan)

## 1. 目标 (Objective)

将项目从基于脚本的结构重构为一个标准的、可安装的 Python 包。这旨在解决当前通过相对路径查找执行脚本所带来的脆弱性，并为项目提供现代化的依赖管理和分发能力。

## 2. 背景与问题 (Background & Problem)

当前 `server.py` 依赖于复杂的路径搜索逻辑来定位和执行 `feedback_ui` 的主程序 `main.py`。这种硬编码的路径关系使得项目结构调整变得困难和危险，任何目录的移动或重命名都可能导致整个应用程序中断。

## 3. 详细任务分解 (Detailed Task Breakdown)

### 任务 3.1: 引入 `pyproject.toml`

- **描述**: 在项目根目录下创建 `pyproject.toml` 文件，作为项目构建和管理的中心配置文件。这是转向现代 Python 打包标准 (PEP 517/518) 的第一步。
- **验收标准**:
    - 项目根目录下存在 `pyproject.toml` 文件。
    - 文件中包含基本的 `[build-system]` 表，指定构建后端（如 `setuptools`）。
    - 文件中包含 `[project]` 表，定义项目元数据（如 `name`, `version`, `authors`）。

### 任务 3.2: 声明项目依赖

- **描述**: 将 `requirements.txt` 或代码中隐含的所有依赖项（如 `PySide6`, `fastmcp`）转移到 `pyproject.toml` 的 `[project.dependencies]` 部分。
- **验收标准**:
    - `pyproject.toml` 中清晰地列出了所有运行时依赖。
    - 项目不再需要 `requirements.txt` 文件。
    - `pip install .` 可以成功安装所有必需的库。

### 任务 3.3: 定义控制台入口点 (Entry Points)

- **描述**: 在 `pyproject.toml` 的 `[project.scripts]` 部分中定义两个控制台脚本入口点：
    - `feedback-server`: 指向 `server.py` 中的主函数。
    - `feedback-ui`: 指向 `main.py` 中的主函数。
- **验收标准**:
    - `pyproject.toml` 中正确配置了两个入口点。
    - 在开发模式下安装 (`pip install -e .`) 后，可以在终端中直接运行 `feedback-server` 和 `feedback-ui` 命令并成功启动相应程序。
    - `server.py` 中调用 `main.py` 的 `subprocess.run` 逻辑需要被重构，改为直接调用 `feedback-ui` 命令。

### 任务 3.4: 项目结构调整

- **描述**: 为了更好地支持打包，可能需要将 `server.py` 和 `main.py` 移动到包目录（例如，一个名为 `src` 的目录或直接在 `feedback_ui` 包的顶层）下，以确保它们能被 `setuptools` 正确找到。
- **验收标准**:
    - 项目文件结构遵循标准的 Python 包布局。
    - 所有导入语句相应更新，以反映新的结构。

## 4. 预期收益 (Expected Benefits)

- **路径解耦**: 彻底消除脚本间的硬编码路径依赖，提高项目结构的灵活性。
- **依赖可靠性**: 依赖关系集中声明，易于管理和复现开发环境。
- **专业化**: 项目结构符合 Python 社区的最佳实践，更易于被其他开发者理解和贡献。
- **易于分发**: 项目可以轻松打包成 wheel 文件，并分发到 PyPI 或私有仓库中。 