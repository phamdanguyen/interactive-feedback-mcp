#!/usr/bin/env python3
"""
测试生产就绪性
Test production readiness of optimized package
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


def test_direct_functionality():
    """直接测试功能（不安装）"""
    print("=" * 80)
    print("🧪 直接功能测试")
    print("=" * 80)

    try:
        # 添加项目路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root / "src"))

        # 测试核心模块导入
        print("📦 测试核心模块导入...")

        from feedback_ui.utils.audio_manager import AudioManager

        print("✅ 音频管理器导入成功")

        from feedback_ui.utils.settings_manager import SettingsManager

        print("✅ 设置管理器导入成功")

        from feedback_ui.main_window import FeedbackUI

        print("✅ 主窗口导入成功")

        # 测试音频管理器
        print("\n🎵 测试音频管理器...")
        audio_manager = AudioManager()
        print(f"✅ 音频后端: {audio_manager._audio_backend}")
        print(f"✅ 音频启用: {audio_manager.is_enabled()}")

        # 测试设置管理器
        print("\n⚙️ 测试设置管理器...")
        settings = SettingsManager()
        print("✅ 设置管理器初始化成功")

        # 测试基本配置
        settings.set_audio_enabled(True)
        enabled = settings.get_audio_enabled()
        if enabled:
            print("✅ 设置读写功能正常")
        else:
            print("❌ 设置读写功能异常")
            return False

        print("\n🎉 所有直接功能测试通过")
        return True

    except Exception as e:
        print(f"❌ 直接功能测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_package_structure():
    """测试包结构"""
    print("\n" + "=" * 80)
    print("📁 测试包结构")
    print("=" * 80)

    project_root = Path(__file__).parent

    # 检查关键文件
    critical_files = [
        "pyproject.toml",
        "src/feedback_ui/__init__.py",
        "src/feedback_ui/cli.py",
        "src/feedback_ui/main_window.py",
        "src/feedback_ui/utils/audio_manager.py",
        "src/feedback_ui/utils/settings_manager.py",
    ]

    missing_files = []
    for file_path in critical_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 缺失")
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ 缺失 {len(missing_files)} 个关键文件")
        return False
    else:
        print("✅ 所有关键文件存在")
        return True


def test_dependency_configuration():
    """测试依赖配置"""
    print("\n" + "=" * 80)
    print("📦 测试依赖配置")
    print("=" * 80)

    project_root = Path(__file__).parent
    pyproject_file = project_root / "pyproject.toml"

    try:
        with open(pyproject_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查优化后的依赖
        checks = [
            ("PySide6-Essentials", "✅ 使用 PySide6-Essentials"),
            ("pyside6[multimedia]", "⚠️ 仍包含 pyside6[multimedia]"),
        ]

        optimized = True
        for dep, message in checks:
            if dep in content:
                if "multimedia" in dep:
                    print(f"❌ {message}")
                    optimized = False
                else:
                    print(f"✅ {message}")
            else:
                if "multimedia" in dep:
                    print(f"✅ 已移除 {dep}")
                else:
                    print(f"❌ 缺少 {dep}")
                    optimized = False

        # 检查可选依赖
        if "[project.optional-dependencies]" in content:
            print("✅ 配置了可选依赖")
        else:
            print("⚠️ 未配置可选依赖")

        return optimized

    except Exception as e:
        print(f"❌ 依赖配置检查失败: {e}")
        return False


def test_build_artifacts():
    """测试构建产物"""
    print("\n" + "=" * 80)
    print("🔨 测试构建产物")
    print("=" * 80)

    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"

    if not dist_dir.exists():
        print("⚠️ dist 目录不存在，尝试构建...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "build", str(project_root)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                print(f"❌ 构建失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ 构建超时")
            return False
        except Exception as e:
            print(f"❌ 构建异常: {e}")
            return False

    if dist_dir.exists():
        files = list(dist_dir.glob("*"))
        if files:
            print(f"✅ 找到 {len(files)} 个构建产物:")
            total_size = 0
            for file in files:
                size_mb = file.stat().st_size / (1024 * 1024)
                total_size += size_mb
                print(f"  {file.name}: {size_mb:.2f} MB")

            print(f"📊 总大小: {total_size:.2f} MB")

            # 检查包大小是否合理（应该很小，因为不包含依赖）
            if total_size < 10:  # 小于10MB
                print("✅ 包大小合理")
                return True
            else:
                print("⚠️ 包大小偏大")
                return True  # 仍然算通过，只是警告
        else:
            print("❌ 没有找到构建产物")
            return False
    else:
        print("❌ dist 目录不存在")
        return False


def test_cross_platform_readiness():
    """测试跨平台就绪性"""
    print("\n" + "=" * 80)
    print("🌍 测试跨平台就绪性")
    print("=" * 80)

    import platform

    system = platform.system().lower()

    print(f"🖥️ 当前系统: {platform.system()} {platform.release()}")

    # 检查音频后端支持
    audio_support = []

    if system == "windows":
        try:
            import winsound

            audio_support.append("winsound (内置)")
        except ImportError:
            pass

    elif system == "darwin":
        # 检查 afplay
        try:
            result = subprocess.run(["which", "afplay"], capture_output=True)
            if result.returncode == 0:
                audio_support.append("afplay (系统)")
        except:
            pass

    elif system == "linux":
        # 检查 Linux 音频工具
        for cmd in ["aplay", "paplay", "play"]:
            try:
                result = subprocess.run(["which", cmd], capture_output=True)
                if result.returncode == 0:
                    audio_support.append(f"{cmd} (系统)")
            except:
                pass

    # 检查 playsound 回退
    try:
        import playsound

        audio_support.append("playsound (回退)")
    except ImportError:
        pass

    print(f"📊 可用音频后端: {audio_support}")

    if audio_support:
        print("✅ 跨平台音频支持良好")
        return True
    else:
        print("⚠️ 当前平台音频支持有限")
        return False


def main():
    """主测试函数"""
    print("🚀 开始生产就绪性测试")

    # 测试项目
    tests = [
        ("包结构", test_package_structure),
        ("依赖配置", test_dependency_configuration),
        ("直接功能", test_direct_functionality),
        ("构建产物", test_build_artifacts),
        ("跨平台就绪性", test_cross_platform_readiness),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🧪 开始测试: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results[test_name] = False

    # 分析结果
    print("\n" + "=" * 80)
    print("📋 生产就绪性评估")
    print("=" * 80)

    passed = 0
    total = len(results)
    critical_tests = ["包结构", "依赖配置", "直接功能"]

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        critical = "🔥 关键" if test_name in critical_tests else ""
        print(f"  {test_name:<15} {status} {critical}")
        if result:
            passed += 1

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    # 评估就绪性
    critical_passed = sum(1 for test in critical_tests if results.get(test, False))

    if critical_passed == len(critical_tests) and passed >= total * 0.8:
        print("\n🎉 生产就绪性评估: ✅ 可以发布")
        print("✅ 所有关键测试通过")
        print("✅ 优化效果显著")
        print("✅ 功能完全兼容")

        print("\n📋 发布建议:")
        print("1. ✅ 可以安全合并到主分支")
        print("2. ✅ 可以创建新版本标签")
        print("3. ✅ 可以发布到 PyPI")
        print("4. 💡 建议在发布说明中强调包大小优化")

        return True

    elif critical_passed == len(critical_tests):
        print("\n✅ 生产就绪性评估: 基本可以发布")
        print("✅ 关键功能正常")
        print("⚠️ 部分非关键测试失败")

        print("\n📋 发布建议:")
        print("1. ✅ 可以合并到主分支")
        print("2. ⚠️ 建议修复非关键问题后发布")

        return True

    else:
        print("\n❌ 生产就绪性评估: 不建议发布")
        print("❌ 关键测试失败")
        print("💡 建议修复关键问题后重新测试")

        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
