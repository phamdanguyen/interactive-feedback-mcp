#!/usr/bin/env python3
"""
测试仅使用 PySide6-Essentials 的包大小
Test package size with PySide6-Essentials only
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


def test_essentials_package_size():
    """测试 PySide6-Essentials 的包大小"""
    print("=" * 80)
    print("📦 PySide6-Essentials 包大小测试")
    print("=" * 80)

    # 创建临时环境
    temp_dir = tempfile.mkdtemp(prefix="test_essentials_")
    env_path = Path(temp_dir)

    print(f"📁 测试环境: {env_path}")

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

        # 安装 PySide6-Essentials
        print("📦 安装 PySide6-Essentials...")
        result = subprocess.run(
            [str(pip_path), "install", "PySide6-Essentials>=6.8.2.1"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ 安装失败: {result.stderr}")
            return None

        print("✅ 安装成功")

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

            # 测试导入
            print("\n🧪 测试导入兼容性...")
            test_imports = [
                "PySide6.QtCore",
                "PySide6.QtGui",
                "PySide6.QtWidgets",
                "PySide6.QtNetwork",
                "PySide6.QtOpenGL",
            ]

            import_results = []
            for module in test_imports:
                try:
                    result = subprocess.run(
                        [
                            str(python_path),
                            "-c",
                            f"import {module}; print('✅ {module}')",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode == 0:
                        import_results.append(f"✅ {module}")
                    else:
                        import_results.append(f"❌ {module}: {result.stderr.strip()}")

                except subprocess.TimeoutExpired:
                    import_results.append(f"⏱️ {module}: 超时")
                except Exception as e:
                    import_results.append(f"❌ {module}: {e}")

            print("📋 导入测试结果:")
            for result in import_results:
                print(f"  {result}")

            # 测试 QtMultimedia 是否不存在（预期行为）
            try:
                result = subprocess.run(
                    [str(python_path), "-c", "import PySide6.QtMultimedia"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode != 0:
                    print("✅ PySide6.QtMultimedia 不可用（符合预期）")
                else:
                    print("⚠️ PySide6.QtMultimedia 仍然可用")

            except Exception as e:
                print(f"❌ QtMultimedia 测试失败: {e}")

            return total_size

        else:
            print(f"❌ site-packages 目录不存在")
            return None

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

    finally:
        # 清理
        try:
            shutil.rmtree(env_path)
            print(f"🗑️ 清理完成")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")


def compare_with_baseline():
    """与基准进行对比"""
    print("\n" + "=" * 80)
    print("📊 与基准配置对比")
    print("=" * 80)

    # 已知的基准数据
    baseline_full_pyside6 = 545.01  # 从之前的测试获得

    # 测试 PySide6-Essentials
    essentials_size = test_essentials_package_size()

    if essentials_size:
        reduction = baseline_full_pyside6 - essentials_size
        reduction_percent = (reduction / baseline_full_pyside6) * 100

        print(f"\n📋 对比结果:")
        print(f"  完整 PySide6:     {baseline_full_pyside6:>8.2f} MB")
        print(f"  PySide6-Essentials: {essentials_size:>8.2f} MB")
        print(f"  减少大小:         {reduction:>8.2f} MB")
        print(f"  减少比例:         {reduction_percent:>8.1f}%")

        if reduction_percent > 80:
            print(f"\n🎉 优化效果优秀！减少了 {reduction_percent:.1f}% 的包大小")
        elif reduction_percent > 50:
            print(f"\n✅ 优化效果良好！减少了 {reduction_percent:.1f}% 的包大小")
        else:
            print(f"\n⚠️ 优化效果有限，仅减少了 {reduction_percent:.1f}% 的包大小")

        return reduction_percent
    else:
        print("❌ 无法进行对比，测试失败")
        return None


def main():
    """主函数"""
    print("🚀 开始 PySide6-Essentials 包大小验证")

    reduction_percent = compare_with_baseline()

    print("\n" + "=" * 80)
    print("📋 验证总结")
    print("=" * 80)

    if reduction_percent:
        print(f"✅ 包大小优化验证完成")
        print(f"📊 实际减少比例: {reduction_percent:.1f}%")

        if reduction_percent >= 85:
            print("🎉 优化目标达成！包大小减少超过 85%")
        elif reduction_percent >= 70:
            print("✅ 优化效果良好！包大小减少超过 70%")
        else:
            print("⚠️ 优化效果低于预期")
    else:
        print("❌ 验证失败")

    print("\n💡 建议:")
    print("- playsound 库可以作为可选依赖")
    print("- 系统原生音频播放已经足够满足需求")
    print("- 可以考虑在文档中说明音频回退机制")


if __name__ == "__main__":
    main()
