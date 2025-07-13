# feedback_ui/utils/audio_manager.py

"""
音频管理器
Audio Manager

提供统一的音频播放接口，支持提示音播放、音量控制等功能。
使用跨平台的原生音频播放，无需 QtMultimedia 依赖。
Provides unified audio playback interface with notification sounds and volume control.
Uses cross-platform native audio playback without QtMultimedia dependency.
"""

import os
import sys
import platform
import subprocess
import threading
from typing import Optional, Union
from pathlib import Path

try:
    from PySide6.QtCore import QObject, Signal

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("警告: PySide6.QtCore 不可用，音频功能将被禁用", file=sys.stderr)

    # 创建虚拟的Signal类用于回退
    class Signal:
        def __init__(self, *_):
            pass

        def connect(self, *_):
            pass

        def emit(self, *_):
            pass

    # 创建虚拟的QObject类用于回退
    class QObject:
        def __init__(self, parent=None):
            pass


class AudioManager(QObject):
    """
    音频管理器类
    Audio Manager Class

    管理应用程序的音频播放功能，包括提示音、音量控制等。
    使用跨平台的原生音频播放，无需 QtMultimedia 依赖。
    Manages application audio playback including notification sounds and volume control.
    Uses cross-platform native audio playback without QtMultimedia dependency.
    """

    # 信号定义
    audio_played = Signal(str)  # 音频播放完成信号
    audio_error = Signal(str)  # 音频播放错误信号

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self._volume: float = 0.5  # 默认音量50%
        self._enabled: bool = True  # 默认启用音频
        self._current_audio_file: Optional[str] = None
        self._system_type = platform.system().lower()
        self._audio_backend: Optional[str] = None

        # 初始化音频系统
        self._initialize_audio()

    def _initialize_audio(self) -> bool:
        """
        初始化音频系统
        Initialize audio system

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检测系统音频播放能力
            if self._system_type == "windows":
                # Windows: 检查是否有 winsound 或 PowerShell
                try:
                    import winsound

                    self._audio_backend = "winsound"
                    print("音频系统初始化成功 (Windows winsound)", file=sys.stderr)
                    return True
                except ImportError:
                    # 回退到 PowerShell
                    self._audio_backend = "powershell"
                    print("音频系统初始化成功 (Windows PowerShell)", file=sys.stderr)
                    return True

            elif self._system_type == "darwin":
                # macOS: 使用 afplay
                self._audio_backend = "afplay"
                print("音频系统初始化成功 (macOS afplay)", file=sys.stderr)
                return True

            elif self._system_type == "linux":
                # Linux: 尝试多种播放器
                for player in ["aplay", "paplay", "play"]:
                    if self._check_command_available(player):
                        self._audio_backend = player
                        print(f"音频系统初始化成功 (Linux {player})", file=sys.stderr)
                        return True

                # 如果都不可用，尝试 playsound 回退
                try:
                    import playsound

                    self._audio_backend = "playsound"
                    print("音频系统初始化成功 (Linux playsound)", file=sys.stderr)
                    return True
                except ImportError:
                    print("Linux 音频播放器不可用，音频功能将被禁用", file=sys.stderr)
                    self._audio_backend = None
                    return False
            else:
                print(f"不支持的操作系统: {self._system_type}", file=sys.stderr)
                self._audio_backend = None
                return False

        except Exception as e:
            print(f"音频系统初始化失败: {e}", file=sys.stderr)
            self._audio_backend = None
            return False

    def _check_command_available(self, command: str) -> bool:
        """检查命令是否可用"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (
            subprocess.SubprocessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def _on_audio_finished(self, audio_file: str):
        """音频播放完成回调"""
        # 播放完成
        if audio_file:
            self.audio_played.emit(audio_file)

    def set_enabled(self, enabled: bool):
        """
        设置音频是否启用
        Set whether audio is enabled

        Args:
            enabled: 是否启用音频
        """
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """
        获取音频是否启用
        Get whether audio is enabled

        Returns:
            bool: 音频是否启用
        """
        return self._enabled and self._audio_backend is not None

    def set_volume(self, volume: Union[int, float]):
        """
        设置音量
        Set volume

        Args:
            volume: 音量值 (0-100 或 0.0-1.0)
        """
        # 标准化音量值到0.0-1.0范围
        if isinstance(volume, int) and volume > 1:
            volume = volume / 100.0

        self._volume = max(0.0, min(1.0, float(volume)))

        # 注意：原生音频播放器通常不支持程序化音量控制
        # 这里保存音量设置主要用于兼容性
        print(
            f"设置音量为 {self._volume:.1%}（原生播放器可能不支持程序化音量控制）",
            file=sys.stderr,
        )

    def get_volume(self) -> float:
        """
        获取当前音量
        Get current volume

        Returns:
            float: 当前音量 (0.0-1.0)
        """
        return self._volume

    def validate_audio_file(self, audio_file: str) -> tuple[bool, str]:
        """
        验证音频文件是否适合作为提示音
        Validate if audio file is suitable for notification sound

        Args:
            audio_file: 音频文件路径

        Returns:
            tuple[bool, str]: (是否有效, 提示信息)
        """
        if not os.path.exists(audio_file):
            return False, "文件不存在"

        # 检查文件大小（建议小于1MB）
        file_size = os.path.getsize(audio_file)
        if file_size > 1024 * 1024:  # 1MB
            return False, f"文件过大 ({file_size // 1024}KB)，建议使用小于1MB的音频文件"

        # 检查文件扩展名
        ext = Path(audio_file).suffix.lower()
        supported_formats = [".wav", ".mp3", ".ogg", ".flac", ".aac"]
        if ext not in supported_formats:
            return False, f"不支持的格式 {ext}，支持: {', '.join(supported_formats)}"

        # 基本验证通过，文件格式和大小都符合要求
        return True, "音频文件有效"

    def play_notification_sound(self, audio_file: Optional[str] = None) -> bool:
        """
        播放提示音
        Play notification sound

        Args:
            audio_file: 音频文件路径，如果为None则使用默认提示音

        Returns:
            bool: 是否成功开始播放
        """
        if not self.is_enabled():
            return False

        if not self._audio_backend:
            print("音频后端不可用", file=sys.stderr)
            return False

        try:
            # 确定要播放的音频文件
            if audio_file is None:
                audio_file = self._get_default_notification_sound()

            # 如果没有音频文件，使用系统默认提示音
            if not audio_file or not os.path.exists(audio_file):
                print(
                    f"音频文件不存在，使用系统默认提示音: {audio_file}", file=sys.stderr
                )
                return self._play_system_notification_sound()

            self._current_audio_file = audio_file

            # 根据后端播放音频
            success = self._play_audio_with_backend(audio_file)

            if success:
                # 异步发送播放完成信号
                threading.Timer(0.1, self._on_audio_finished, args=[audio_file]).start()

            return success

        except Exception as e:
            print(f"播放提示音失败: {e}", file=sys.stderr)
            self.audio_error.emit(str(e))
            return False

    def _play_audio_with_backend(self, audio_file: str) -> bool:
        """使用指定后端播放音频"""
        try:
            if self._audio_backend == "winsound":
                import winsound

                # 异步播放
                winsound.PlaySound(
                    audio_file, winsound.SND_FILENAME | winsound.SND_ASYNC
                )
                return True

            elif self._audio_backend == "powershell":
                # Windows PowerShell 播放
                cmd = f'powershell -c "(New-Object Media.SoundPlayer \\"{audio_file}\\").PlaySync()"'
                subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

            elif self._audio_backend == "afplay":
                # macOS afplay
                subprocess.Popen(
                    ["afplay", audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

            elif self._audio_backend in ["aplay", "paplay", "play"]:
                # Linux 音频播放器
                subprocess.Popen(
                    [self._audio_backend, audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

            elif self._audio_backend == "playsound":
                # 跨平台回退方案
                try:
                    import playsound

                    # 异步播放
                    threading.Thread(
                        target=playsound.playsound,
                        args=[audio_file, False],
                        daemon=True,
                    ).start()
                    return True
                except Exception as e:
                    print(f"playsound 播放失败: {e}", file=sys.stderr)
                    return False

            else:
                print(f"未知的音频后端: {self._audio_backend}", file=sys.stderr)
                return False

        except Exception as e:
            print(f"音频播放失败: {e}", file=sys.stderr)
            return False

    def _get_default_notification_sound(self) -> Optional[str]:
        """
        获取默认提示音文件路径
        Get default notification sound file path

        Returns:
            str: 默认提示音文件路径
        """
        # 优先尝试从包内资源获取
        try:
            # 获取当前文件所在目录
            current_dir = Path(__file__).parent.parent
            sound_file = current_dir / "resources" / "sounds" / "notification.wav"

            if sound_file.exists():
                return str(sound_file)
            else:
                print(f"包内默认提示音文件不存在: {sound_file}", file=sys.stderr)
        except Exception as e:
            print(f"获取包内音频文件失败: {e}", file=sys.stderr)

        # 回退：尝试从Qt资源系统获取
        resource_path = ":/sounds/notification.wav"
        if self._check_qt_resource(resource_path):
            return resource_path

        # 最后回退：使用系统默认提示音
        print("使用系统默认提示音", file=sys.stderr)
        return None

    def _play_system_notification_sound(self) -> bool:
        """
        播放系统默认提示音
        Play system default notification sound

        Returns:
            bool: 是否成功播放
        """
        try:
            if self._system_type == "windows":
                # Windows 系统默认提示音
                if self._audio_backend == "winsound":
                    import winsound

                    winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    return True
                elif self._audio_backend == "powershell":
                    # PowerShell 播放系统提示音
                    cmd = 'powershell -c "[console]::beep(800,200)"'
                    subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True

            elif self._system_type == "darwin":
                # macOS 系统默认提示音
                subprocess.Popen(
                    ["afplay", "/System/Library/Sounds/Glass.aiff"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

            elif self._system_type == "linux":
                # Linux 系统提示音 (通过终端铃声)
                print("\a", end="", flush=True)  # 终端铃声
                return True

            return False

        except Exception as e:
            print(f"播放系统提示音失败: {e}", file=sys.stderr)
            return False

    def _check_qt_resource(self, resource_path: str) -> bool:
        """
        检查Qt资源是否存在
        Check if Qt resource exists

        Args:
            resource_path: Qt资源路径

        Returns:
            bool: 资源是否存在
        """
        try:
            if PYSIDE6_AVAILABLE:
                from PySide6.QtCore import QFile

                return QFile.exists(resource_path)
            else:
                return False
        except:
            return False

    def stop_current_sound(self):
        """
        停止当前播放的音频
        Stop currently playing audio

        注意：由于使用原生音频播放，无法精确控制停止，
        此方法主要用于兼容性，实际效果有限。
        """
        # 原生音频播放通常无法精确停止，这里主要用于兼容性
        print("停止音频播放请求（原生播放器可能无法精确停止）", file=sys.stderr)

    def is_playing(self) -> bool:
        """
        检查是否正在播放音频
        Check if audio is currently playing

        Returns:
            bool: 是否正在播放

        注意：由于使用原生音频播放，无法精确检测播放状态，
        此方法主要用于兼容性，始终返回 False。
        """
        # 原生音频播放无法精确检测状态，为了兼容性返回 False
        return False


# 全局音频管理器实例
_global_audio_manager: Optional[AudioManager] = None


def get_audio_manager() -> Optional[AudioManager]:
    """
    获取全局音频管理器实例
    Get global audio manager instance

    Returns:
        AudioManager: 音频管理器实例
    """
    global _global_audio_manager

    if _global_audio_manager is None:
        _global_audio_manager = AudioManager()

    return _global_audio_manager


# 移除了便捷函数，直接使用 get_audio_manager().play_notification_sound() 更清晰
