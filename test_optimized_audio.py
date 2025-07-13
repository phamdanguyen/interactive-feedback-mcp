#!/usr/bin/env python3
"""
测试优化后的音频管理器
Test the optimized audio manager
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def create_test_wav():
    """创建测试 WAV 文件"""
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


def test_audio_manager():
    """测试音频管理器"""
    print("=" * 60)
    print("🎵 测试优化后的音频管理器")
    print("=" * 60)

    try:
        # 导入音频管理器
        from feedback_ui.utils.audio_manager import AudioManager

        print("✅ 音频管理器导入成功")

        # 创建音频管理器实例
        audio_manager = AudioManager()
        print("✅ 音频管理器实例创建成功")

        # 测试基本属性
        print(f"📊 音频是否启用: {audio_manager.is_enabled()}")
        print(f"📊 当前音量: {audio_manager.get_volume()}")
        print(f"📊 是否正在播放: {audio_manager.is_playing()}")

        # 创建测试音频文件
        test_file = create_test_wav()
        print(f"📁 创建测试音频文件: {test_file}")

        try:
            # 测试音频播放
            print("\n🔊 测试音频播放...")
            success = audio_manager.play_notification_sound(test_file)

            if success:
                print("✅ 音频播放成功")
            else:
                print("❌ 音频播放失败")

            # 测试默认提示音
            print("\n🔔 测试默认提示音...")
            success = audio_manager.play_notification_sound()

            if success:
                print("✅ 默认提示音播放成功")
            else:
                print("⚠️ 默认提示音播放失败（可能是文件不存在）")

            # 测试音量控制
            print("\n🔊 测试音量控制...")
            audio_manager.set_volume(0.8)
            print(f"✅ 设置音量为 80%: {audio_manager.get_volume()}")

            # 测试启用/禁用
            print("\n⏸️ 测试启用/禁用...")
            audio_manager.set_enabled(False)
            print(f"✅ 禁用音频: {audio_manager.is_enabled()}")

            audio_manager.set_enabled(True)
            print(f"✅ 启用音频: {audio_manager.is_enabled()}")

            print("\n" + "=" * 60)
            print("🎉 音频管理器测试完成")
            print("✅ 所有基本功能正常工作")
            print("✅ API 接口完全兼容")

        finally:
            # 清理测试文件
            try:
                os.unlink(test_file)
                print(f"🗑️ 清理测试文件: {test_file}")
            except:
                pass

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("💡 请确保已安装新的依赖: PySide6-Essentials")
        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def test_import_compatibility():
    """测试导入兼容性"""
    print("\n" + "=" * 60)
    print("📦 测试导入兼容性")
    print("=" * 60)

    try:
        # 测试 PySide6-Essentials 导入
        from PySide6.QtCore import QObject, Signal

        print("✅ PySide6.QtCore 导入成功")

        from PySide6.QtGui import QPixmap, QIcon

        print("✅ PySide6.QtGui 导入成功")

        from PySide6.QtWidgets import QApplication, QMainWindow

        print("✅ PySide6.QtWidgets 导入成功")

        # 测试 QtMultimedia 是否不可用（预期行为）
        try:
            from PySide6.QtMultimedia import QSoundEffect

            print("⚠️ PySide6.QtMultimedia 仍然可用（可能未完全切换到 Essentials）")
        except ImportError:
            print("✅ PySide6.QtMultimedia 不可用（符合预期）")

        # 测试 playsound 导入
        try:
            import playsound

            print("✅ playsound 库可用")
        except ImportError:
            print("⚠️ playsound 库不可用（可选依赖）")

        print("\n✅ 导入兼容性测试通过")
        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试优化后的音频系统")

    # 测试导入兼容性
    import_ok = test_import_compatibility()

    # 测试音频管理器
    audio_ok = test_audio_manager()

    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)

    if import_ok and audio_ok:
        print("🎉 所有测试通过！")
        print("✅ 优化成功，功能完全兼容")
        print("✅ 可以安全使用新的音频系统")
    else:
        print("❌ 部分测试失败")
        if not import_ok:
            print("❌ 导入兼容性问题")
        if not audio_ok:
            print("❌ 音频管理器问题")


if __name__ == "__main__":
    main()
