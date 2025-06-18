#!/usr/bin/env python3
"""
Interactive Feedback MCP - 安装验证脚本
Installation Verification Script

用于验证项目依赖是否正确安装
Used to verify that project dependencies are correctly installed
"""

import sys
import importlib
from typing import List, Tuple


def check_python_version() -> bool:
    """检查 Python 版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python 版本过低: {version.major}.{version.minor}.{version.micro} (需要 >= 3.11)"
        )
        return False


def check_dependencies() -> List[Tuple[str, bool, str]]:
    """检查依赖包"""
    dependencies = [
        ("fastmcp", "MCP 核心库"),
        ("psutil", "系统进程信息"),
        ("PySide6", "GUI 框架"),
        ("pyperclip", "剪贴板操作"),
        ("PIL", "图像处理 (Pillow)"),
        ("openai", "AI 提供商支持"),
    ]

    # Windows 特定依赖
    if sys.platform == "win32":
        dependencies.append(("win32api", "Windows API (pywin32)"))

    results = []

    for package, description in dependencies:
        try:
            importlib.import_module(package)
            print(f"✅ {package}: {description}")
            results.append((package, True, description))
        except ImportError:
            print(f"❌ {package}: {description} - 未安装")
            results.append((package, False, description))

    return results


def check_project_structure() -> bool:
    """检查项目结构"""
    import os
    from pathlib import Path

    required_files = [
        "pyproject.toml",
        "requirements.txt",
        "src/interactive_feedback_server",
        "src/feedback_ui",
    ]

    project_root = Path(__file__).parent
    all_exist = True

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 文件/目录不存在")
            all_exist = False

    return all_exist


def main():
    """主函数"""
    print("🔍 Interactive Feedback MCP - 安装验证")
    print("=" * 50)

    # 检查 Python 版本
    print("\n📋 检查 Python 版本:")
    python_ok = check_python_version()

    # 检查依赖
    print("\n📦 检查依赖包:")
    dep_results = check_dependencies()
    deps_ok = all(result[1] for result in dep_results)

    # 检查项目结构
    print("\n📁 检查项目结构:")
    structure_ok = check_project_structure()

    # 总结
    print("\n" + "=" * 50)
    print("📊 验证结果:")

    if python_ok and deps_ok and structure_ok:
        print("🎉 所有检查通过！项目已正确安装。")
        print("\n🚀 您可以开始使用 Interactive Feedback MCP 了！")
        return 0
    else:
        print("⚠️  发现问题，请检查上述错误信息。")

        if not python_ok:
            print("   - 请升级到 Python 3.11 或更高版本")

        if not deps_ok:
            print("   - 请安装缺失的依赖包:")
            print("     uv pip install -e . 或 uv pip install -r requirements.txt")

        if not structure_ok:
            print("   - 请确保在正确的项目目录中运行此脚本")

        return 1


if __name__ == "__main__":
    sys.exit(main())
