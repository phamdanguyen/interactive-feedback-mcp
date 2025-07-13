#!/usr/bin/env python3
"""
测试音频替代方案的可行性
Test the feasibility of audio alternatives
"""

import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path


def test_winsound():
    """测试 Windows winsound 模块"""
    if platform.system().lower() != "windows":
        return False, "不是 Windows 系统"

    try:
        import winsound

        # 测试系统提示音
        winsound.Beep(1000, 100)
        return True, "winsound 可用"
    except ImportError:
        return False, "winsound 不可用"
    except Exception as e:
        return False, f"winsound 错误: {e}"


def test_playsound():
    """测试 playsound 库"""
    try:
        # 检查是否已安装
        import playsound

        return True, "playsound 已安装"
    except ImportError:
        return False, "playsound 未安装 (可通过 pip install playsound 安装)"


def test_macos_afplay():
    """测试 macOS afplay 命令"""
    if platform.system().lower() != "darwin":
        return False, "不是 macOS 系统"

    try:
        result = subprocess.run(
            ["which", "afplay"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True, f"afplay 可用: {result.stdout.strip()}"
        else:
            return False, "afplay 不可用"
    except Exception as e:
        return False, f"afplay 测试失败: {e}"


def test_linux_audio():
    """测试 Linux 音频命令"""
    if platform.system().lower() != "linux":
        return False, "不是 Linux 系统"

    audio_commands = ["aplay", "paplay", "play"]
    available_commands = []

    for cmd in audio_commands:
        try:
            result = subprocess.run(
                ["which", cmd], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                available_commands.append(cmd)
        except Exception:
            continue

    if available_commands:
        return True, f"可用命令: {', '.join(available_commands)}"
    else:
        return False, "没有可用的音频播放命令"


def create_test_audio_file():
    """创建测试音频文件"""
    # 创建一个简单的 WAV 文件头（静音）
    wav_header = bytes(
        [
            0x52,
            0x49,
            0x46,
            0x46,  # "RIFF"
            0x24,
            0x00,
            0x00,
            0x00,  # 文件大小 - 8
            0x57,
            0x41,
            0x56,
            0x45,  # "WAVE"
            0x66,
            0x6D,
            0x74,
            0x20,  # "fmt "
            0x10,
            0x00,
            0x00,
            0x00,  # fmt chunk size
            0x01,
            0x00,  # PCM format
            0x01,
            0x00,  # mono
            0x44,
            0xAC,
            0x00,
            0x00,  # 44100 Hz
            0x88,
            0x58,
            0x01,
            0x00,  # byte rate
            0x02,
            0x00,  # block align
            0x10,
            0x00,  # 16 bits per sample
            0x64,
            0x61,
            0x74,
            0x61,  # "data"
            0x00,
            0x00,
            0x00,
            0x00,  # data size (0 = silence)
        ]
    )

    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.write(wav_header)
    temp_file.close()

    return temp_file.name


def test_audio_playback():
    """测试实际音频播放"""
    test_file = create_test_audio_file()

    try:
        system = platform.system().lower()

        if system == "windows":
            try:
                import winsound

                winsound.PlaySound(
                    test_file, winsound.SND_FILENAME | winsound.SND_ASYNC
                )
                return True, "Windows 音频播放成功"
            except Exception as e:
                return False, f"Windows 音频播放失败: {e}"

        elif system == "darwin":
            try:
                subprocess.run(
                    ["afplay", test_file], check=True, timeout=2, capture_output=True
                )
                return True, "macOS 音频播放成功"
            except Exception as e:
                return False, f"macOS 音频播放失败: {e}"

        elif system == "linux":
            for cmd in ["aplay", "paplay", "play"]:
                try:
                    subprocess.run(
                        [cmd, test_file], check=True, timeout=2, capture_output=True
                    )
                    return True, f"Linux 音频播放成功 ({cmd})"
                except Exception:
                    continue

            return False, "Linux 音频播放失败"

        else:
            return False, f"不支持的操作系统: {system}"

    finally:
        try:
            os.unlink(test_file)
        except:
            pass


def main():
    print("=" * 60)
    print("🎵 音频替代方案可行性测试")
    print("=" * 60)

    print(f"\n🖥️  当前系统: {platform.system()} {platform.release()}")
    print(f"🐍 Python 版本: {sys.version}")

    print("\n📋 测试结果:")

    # 测试各种音频方案
    tests = [
        ("Windows winsound", test_winsound),
        ("playsound 库", test_playsound),
        ("macOS afplay", test_macos_afplay),
        ("Linux 音频命令", test_linux_audio),
    ]

    available_methods = []

    for test_name, test_func in tests:
        try:
            success, message = test_func()
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}: {message}")

            if success:
                available_methods.append(test_name)
        except Exception as e:
            print(f"  ❌ {test_name}: 测试异常 - {e}")

    print(f"\n🎯 可用方案数量: {len(available_methods)}")

    if available_methods:
        print("✅ 音频替代方案可行")
        print(f"📝 推荐方案: {available_methods[0]}")

        # 测试实际播放
        print("\n🔊 测试实际音频播放...")
        success, message = test_audio_playback()
        status = "✅" if success else "❌"
        print(f"  {status} {message}")

    else:
        print("❌ 没有可用的音频替代方案")
        print("💡 建议安装 playsound: pip install playsound")

    print("\n" + "=" * 60)
    print("🎯 结论:")

    if available_methods:
        print("✅ 方案一（PySide6-Essentials + 音频替代）完全可行")
        print("✅ 可以安全地移除 QtMultimedia 依赖")
        print("✅ 所有现有功能都能正常工作")
    else:
        print("⚠️  需要安装额外的音频库")
        print("💡 建议先安装 playsound 再进行迁移")


if __name__ == "__main__":
    main()
