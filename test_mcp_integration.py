#!/usr/bin/env python3
"""
测试 MCP 服务集成
Test MCP service integration with optimized dependencies
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path


def test_mcp_service_installation():
    """测试 MCP 服务安装"""
    print("=" * 80)
    print("🔧 测试 MCP 服务安装")
    print("=" * 80)

    # 创建临时环境
    temp_dir = tempfile.mkdtemp(prefix="mcp_test_")
    env_path = Path(temp_dir)

    print(f"📁 测试环境: {env_path}")

    try:
        # 创建虚拟环境
        subprocess.run(
            [sys.executable, "-m", "venv", str(env_path)],
            check=True,
            capture_output=True,
        )

        # 获取路径
        if os.name == "nt":  # Windows
            pip_path = env_path / "Scripts" / "pip.exe"
            python_path = env_path / "Scripts" / "python.exe"
        else:  # Unix-like
            pip_path = env_path / "bin" / "pip"
            python_path = env_path / "bin" / "python"

        # 升级 pip
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )

        # 安装当前项目（使用优化后的依赖）
        print("📦 安装当前项目...")
        project_root = Path(__file__).parent

        result = subprocess.run(
            [str(pip_path), "install", "-e", str(project_root)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ 项目安装失败:")
            print(result.stderr)
            return False

        print("✅ 项目安装成功")

        # 测试 MCP 服务启动
        print("\n🚀 测试 MCP 服务启动...")

        # 创建测试配置
        test_config = {
            "display_mode": "simple",
            "ui": {
                "window_size": {"width": 800, "height": 600},
                "button_size": {"width": 100, "height": 35},
            },
            "audio": {"enabled": True, "volume": 0.5},
        }

        config_file = env_path / "test_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=2)

        # 测试 CLI 启动（不实际显示 UI）
        test_script = f"""
import sys
sys.path.insert(0, r"{project_root / 'src'}")

try:
    from feedback_ui.cli import main
    from feedback_ui.utils.audio_manager import AudioManager
    
    print("✅ CLI 模块导入成功")
    
    # 测试音频管理器
    audio_manager = AudioManager()
    print(f"✅ 音频管理器初始化成功: {{audio_manager._audio_backend}}")
    
    # 测试配置加载
    from feedback_ui.utils.settings_manager import SettingsManager
    settings = SettingsManager()
    print("✅ 设置管理器初始化成功")
    
    print("🎉 所有核心组件测试通过")
    
except Exception as e:
    print(f"❌ 测试失败: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        result = subprocess.run(
            [str(python_path), "-c", test_script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ MCP 服务核心功能测试通过")
            print(result.stdout)
            return True
        else:
            print("❌ MCP 服务测试失败")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ 测试过程失败: {e}")
        return False

    finally:
        # 清理
        try:
            shutil.rmtree(env_path)
            print(f"🗑️ 清理测试环境完成")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")


def test_package_build():
    """测试包构建"""
    print("\n" + "=" * 80)
    print("📦 测试包构建")
    print("=" * 80)

    project_root = Path(__file__).parent

    try:
        # 检查 pyproject.toml
        pyproject_file = project_root / "pyproject.toml"
        if not pyproject_file.exists():
            print("❌ pyproject.toml 不存在")
            return False

        print("✅ pyproject.toml 存在")

        # 检查依赖配置
        with open(pyproject_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "PySide6-Essentials" in content:
            print("✅ 使用 PySide6-Essentials 依赖")
        else:
            print("⚠️ 未找到 PySide6-Essentials 依赖")

        if "pyside6[multimedia]" in content:
            print("⚠️ 仍然包含 pyside6[multimedia] 依赖")
        else:
            print("✅ 已移除 pyside6[multimedia] 依赖")

        # 测试构建（如果有 build 工具）
        try:
            result = subprocess.run(
                [sys.executable, "-m", "build", "--version"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ build 工具可用")

                # 尝试构建
                print("🔨 尝试构建包...")
                result = subprocess.run(
                    [sys.executable, "-m", "build", str(project_root)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode == 0:
                    print("✅ 包构建成功")

                    # 检查构建产物
                    dist_dir = project_root / "dist"
                    if dist_dir.exists():
                        files = list(dist_dir.glob("*"))
                        print(f"📋 构建产物: {len(files)} 个文件")
                        for file in files:
                            size_mb = file.stat().st_size / (1024 * 1024)
                            print(f"  {file.name}: {size_mb:.2f} MB")

                    return True
                else:
                    print("❌ 包构建失败")
                    print(result.stderr)
                    return False
            else:
                print("⚠️ build 工具不可用，跳过构建测试")
                return True

        except subprocess.TimeoutExpired:
            print("⏱️ 构建超时")
            return False

    except Exception as e:
        print(f"❌ 构建测试失败: {e}")
        return False


def test_cross_platform_compatibility():
    """测试跨平台兼容性"""
    print("\n" + "=" * 80)
    print("🌍 测试跨平台兼容性")
    print("=" * 80)

    import platform

    system = platform.system().lower()

    print(f"🖥️ 当前系统: {platform.system()} {platform.release()}")

    # 测试音频后端
    audio_backends = []

    if system == "windows":
        try:
            import winsound

            winsound.Beep(1000, 50)
            audio_backends.append("winsound")
        except:
            pass

    elif system == "darwin":
        try:
            result = subprocess.run(["which", "afplay"], capture_output=True)
            if result.returncode == 0:
                audio_backends.append("afplay")
        except:
            pass

    elif system == "linux":
        for cmd in ["aplay", "paplay", "play"]:
            try:
                result = subprocess.run(["which", cmd], capture_output=True)
                if result.returncode == 0:
                    audio_backends.append(cmd)
            except:
                pass

    print(f"📊 可用音频后端: {audio_backends}")

    if audio_backends:
        print("✅ 跨平台音频兼容性良好")
        return True
    else:
        print("⚠️ 没有可用的音频后端")
        return False


def main():
    """主测试函数"""
    print("🚀 开始 MCP 服务集成测试")

    # 运行各项测试
    tests = [
        ("MCP 服务安装", test_mcp_service_installation),
        ("包构建", test_package_build),
        ("跨平台兼容性", test_cross_platform_compatibility),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🧪 开始测试: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results[test_name] = False

    # 总结结果
    print("\n" + "=" * 80)
    print("📋 集成测试总结")
    print("=" * 80)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<20} {status}")
        if result:
            passed += 1

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有集成测试通过！")
        print("✅ 优化版本可以安全发布")
    elif passed >= total * 0.8:
        print("✅ 大部分测试通过，可以考虑发布")
        print("💡 建议修复失败的测试后再发布")
    else:
        print("⚠️ 多项测试失败，建议修复后再发布")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
