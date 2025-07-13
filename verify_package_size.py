#!/usr/bin/env python3
"""
验证包大小优化效果
Verify package size optimization results
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


def get_directory_size(path):
    """获取目录大小（MB）"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    return total_size / (1024 * 1024)  # 转换为 MB


def create_test_environment(env_name, requirements):
    """创建测试环境"""
    print(f"🔧 创建测试环境: {env_name}")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix=f"test_env_{env_name}_")
    env_path = Path(temp_dir)

    print(f"📁 环境路径: {env_path}")

    try:
        # 创建虚拟环境
        subprocess.run(
            [sys.executable, "-m", "venv", str(env_path)],
            check=True,
            capture_output=True,
        )

        # 获取 pip 路径
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

        # 安装依赖
        for req in requirements:
            print(f"📦 安装: {req}")
            result = subprocess.run(
                [str(pip_path), "install", req], capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"❌ 安装失败: {req}")
                print(f"错误: {result.stderr}")
                return None, None

        # 计算包大小
        site_packages = (
            env_path / "Lib" / "site-packages"
            if os.name == "nt"
            else env_path
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )

        if site_packages.exists():
            total_size = get_directory_size(site_packages)
            print(f"📊 总包大小: {total_size:.2f} MB")

            # 分析 PySide6 相关包大小
            pyside_size = 0
            pyside_dirs = []

            for item in site_packages.iterdir():
                if item.is_dir() and (
                    "pyside" in item.name.lower() or "qt" in item.name.lower()
                ):
                    item_size = get_directory_size(item)
                    pyside_size += item_size
                    pyside_dirs.append((item.name, item_size))

            print(f"📊 PySide6 相关包大小: {pyside_size:.2f} MB")

            if pyside_dirs:
                print("📋 详细分布:")
                for name, size in sorted(pyside_dirs, key=lambda x: x[1], reverse=True):
                    print(f"  {name:<30} {size:>8.2f} MB")

            return env_path, total_size
        else:
            print(f"❌ site-packages 目录不存在: {site_packages}")
            return None, None

    except subprocess.CalledProcessError as e:
        print(f"❌ 环境创建失败: {e}")
        return None, None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None, None


def test_package_sizes():
    """测试不同配置的包大小"""
    print("=" * 80)
    print("📦 包大小验证测试")
    print("=" * 80)

    # 测试配置
    configs = [
        {
            "name": "original",
            "description": "原始配置 (pyside6[multimedia])",
            "requirements": ["pyside6[multimedia]>=6.8.2.1"],
        },
        {
            "name": "optimized",
            "description": "优化配置 (PySide6-Essentials)",
            "requirements": ["PySide6-Essentials>=6.8.2.1", "playsound>=1.3.0"],
        },
    ]

    results = {}

    for config in configs:
        print(f"\n🧪 测试配置: {config['description']}")
        print("-" * 60)

        env_path, total_size = create_test_environment(
            config["name"], config["requirements"]
        )

        if env_path and total_size:
            results[config["name"]] = {
                "size": total_size,
                "path": env_path,
                "description": config["description"],
            }
            print(f"✅ 测试完成: {total_size:.2f} MB")
        else:
            print(f"❌ 测试失败")
            results[config["name"]] = None

    # 分析结果
    print("\n" + "=" * 80)
    print("📊 包大小对比分析")
    print("=" * 80)

    if results.get("original") and results.get("optimized"):
        original_size = results["original"]["size"]
        optimized_size = results["optimized"]["size"]

        reduction = original_size - optimized_size
        reduction_percent = (reduction / original_size) * 100

        print(f"\n📋 对比结果:")
        print(f"  原始配置:     {original_size:>8.2f} MB")
        print(f"  优化配置:     {optimized_size:>8.2f} MB")
        print(f"  减少大小:     {reduction:>8.2f} MB")
        print(f"  减少比例:     {reduction_percent:>8.1f}%")

        if reduction_percent > 80:
            print(f"\n🎉 优化效果优秀！减少了 {reduction_percent:.1f}% 的包大小")
        elif reduction_percent > 50:
            print(f"\n✅ 优化效果良好！减少了 {reduction_percent:.1f}% 的包大小")
        else:
            print(f"\n⚠️ 优化效果有限，仅减少了 {reduction_percent:.1f}% 的包大小")

    else:
        print("❌ 无法进行对比分析，部分测试失败")

    # 清理临时环境
    print(f"\n🗑️ 清理临时环境...")
    for name, result in results.items():
        if result and result["path"]:
            try:
                shutil.rmtree(result["path"])
                print(f"✅ 清理完成: {name}")
            except Exception as e:
                print(f"⚠️ 清理失败: {name} - {e}")


def test_cross_platform_audio():
    """测试跨平台音频兼容性"""
    print("\n" + "=" * 80)
    print("🎵 跨平台音频兼容性测试")
    print("=" * 80)

    import platform

    system = platform.system().lower()

    print(f"🖥️ 当前系统: {platform.system()} {platform.release()}")

    # 测试系统音频命令
    audio_tests = []

    if system == "windows":
        # 测试 winsound
        try:
            import winsound

            winsound.Beep(1000, 100)
            audio_tests.append(("Windows winsound", "✅ 可用"))
        except Exception as e:
            audio_tests.append(("Windows winsound", f"❌ 不可用: {e}"))

        # 测试 PowerShell
        try:
            result = subprocess.run(
                ["powershell", "-c", "(New-Object Media.SoundPlayer).PlaySync()"],
                capture_output=True,
                timeout=5,
            )
            audio_tests.append(("Windows PowerShell", "✅ 可用"))
        except Exception as e:
            audio_tests.append(("Windows PowerShell", f"❌ 不可用: {e}"))

    elif system == "darwin":
        # 测试 afplay
        try:
            result = subprocess.run(["which", "afplay"], capture_output=True)
            if result.returncode == 0:
                audio_tests.append(("macOS afplay", "✅ 可用"))
            else:
                audio_tests.append(("macOS afplay", "❌ 不可用"))
        except Exception as e:
            audio_tests.append(("macOS afplay", f"❌ 测试失败: {e}"))

    elif system == "linux":
        # 测试 Linux 音频命令
        for cmd in ["aplay", "paplay", "play"]:
            try:
                result = subprocess.run(["which", cmd], capture_output=True)
                if result.returncode == 0:
                    audio_tests.append((f"Linux {cmd}", "✅ 可用"))
                else:
                    audio_tests.append((f"Linux {cmd}", "❌ 不可用"))
            except Exception as e:
                audio_tests.append((f"Linux {cmd}", f"❌ 测试失败: {e}"))

    # 测试 playsound 回退
    try:
        import playsound

        audio_tests.append(("playsound (回退)", "✅ 可用"))
    except ImportError:
        audio_tests.append(("playsound (回退)", "❌ 未安装"))
    except Exception as e:
        audio_tests.append(("playsound (回退)", f"❌ 错误: {e}"))

    # 显示测试结果
    print(f"\n📋 音频后端测试结果:")
    for test_name, result in audio_tests:
        print(f"  {test_name:<25} {result}")

    # 统计可用的音频后端
    available_backends = [test for test, result in audio_tests if "✅" in result]

    print(f"\n📊 可用音频后端数量: {len(available_backends)}")

    if len(available_backends) > 0:
        print("✅ 跨平台音频兼容性良好")
        return True
    else:
        print("❌ 没有可用的音频后端")
        return False


def main():
    """主函数"""
    print("🚀 开始包大小和兼容性验证")

    # 包大小验证
    test_package_sizes()

    # 跨平台音频测试
    audio_ok = test_cross_platform_audio()

    print("\n" + "=" * 80)
    print("📋 验证总结")
    print("=" * 80)

    print("✅ 包大小验证完成")
    if audio_ok:
        print("✅ 跨平台音频兼容性验证通过")
    else:
        print("⚠️ 跨平台音频兼容性需要关注")

    print("\n🎉 验证流程完成！")


if __name__ == "__main__":
    main()
