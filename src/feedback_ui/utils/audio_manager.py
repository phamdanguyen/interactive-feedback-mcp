# feedback_ui/utils/audio_manager.py

"""
音频管理器
Audio Manager

提供统一的音频播放接口，支持提示音播放、音量控制等功能。
Provides unified audio playback interface with notification sounds and volume control.
"""

import os
import sys
from typing import Optional, Union
from pathlib import Path

try:
    from PySide6.QtCore import QObject, QUrl, Signal
    from PySide6.QtMultimedia import QSoundEffect

    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False
    print("警告: PySide6.QtMultimedia 不可用，音频功能将被禁用", file=sys.stderr)

    # 创建虚拟的Signal类用于回退
    class Signal:
        def __init__(self, *_):
            pass

        def connect(self, *_):
            pass

        def emit(self, *_):
            pass


class AudioManager(QObject):
    """
    音频管理器类
    Audio Manager Class

    管理应用程序的音频播放功能，包括提示音、音量控制等。
    Manages application audio playback including notification sounds and volume control.
    """

    # 信号定义
    audio_played = Signal(str)  # 音频播放完成信号
    audio_error = Signal(str)  # 音频播放错误信号

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self._sound_effect: Optional[QSoundEffect] = None
        self._volume: float = 0.5  # 默认音量50%
        self._enabled: bool = True  # 默认启用音频
        self._current_audio_file: Optional[str] = None

        # 初始化音频系统
        self._initialize_audio()

    def _initialize_audio(self) -> bool:
        """
        初始化音频系统
        Initialize audio system

        Returns:
            bool: 初始化是否成功
        """
        if not MULTIMEDIA_AVAILABLE:
            print("音频系统不可用，跳过初始化", file=sys.stderr)
            return False

        try:
            self._sound_effect = QSoundEffect(self)

            # 连接信号
            if hasattr(self._sound_effect, "playingChanged"):
                self._sound_effect.playingChanged.connect(self._on_playing_changed)

            # 设置默认属性
            self._sound_effect.setVolume(self._volume)

            print("音频系统初始化成功", file=sys.stderr)
            return True

        except Exception as e:
            print(f"音频系统初始化失败: {e}", file=sys.stderr)
            self._sound_effect = None
            return False

    def _on_playing_changed(self):
        """音频播放状态变化回调"""
        if self._sound_effect and not self._sound_effect.isPlaying():
            # 播放完成
            if self._current_audio_file:
                self.audio_played.emit(self._current_audio_file)

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
        return self._enabled and MULTIMEDIA_AVAILABLE and self._sound_effect is not None

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

        if self._sound_effect:
            self._sound_effect.setVolume(self._volume)

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

        try:
            # 确定要播放的音频文件
            if audio_file is None:
                audio_file = self._get_default_notification_sound()

            if not audio_file or not os.path.exists(audio_file):
                print(f"音频文件不存在: {audio_file}", file=sys.stderr)
                return False

            # 设置音频源
            audio_url = QUrl.fromLocalFile(audio_file)
            self._sound_effect.setSource(audio_url)
            self._current_audio_file = audio_file

            # 播放音频
            self._sound_effect.play()
            return True

        except Exception as e:
            print(f"播放提示音失败: {e}", file=sys.stderr)
            self.audio_error.emit(str(e))
            return False

    def _get_default_notification_sound(self) -> Optional[str]:
        """
        获取默认提示音文件路径
        Get default notification sound file path

        Returns:
            str: 默认提示音文件路径
        """
        # 尝试从Qt资源系统获取
        resource_path = ":/sounds/notification.wav"

        # 如果资源系统不可用，尝试从文件系统获取
        if not self._check_qt_resource(resource_path):
            # 获取当前文件所在目录
            current_dir = Path(__file__).parent.parent
            sound_file = current_dir / "resources" / "sounds" / "notification.wav"

            if sound_file.exists():
                return str(sound_file)
            else:
                print(f"默认提示音文件不存在: {sound_file}", file=sys.stderr)
                return None

        return resource_path

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
            from PySide6.QtCore import QFile

            return QFile.exists(resource_path)
        except:
            return False

    def stop_current_sound(self):
        """
        停止当前播放的音频
        Stop currently playing audio
        """
        if self._sound_effect and self._sound_effect.isPlaying():
            self._sound_effect.stop()

    def is_playing(self) -> bool:
        """
        检查是否正在播放音频
        Check if audio is currently playing

        Returns:
            bool: 是否正在播放
        """
        return self._sound_effect is not None and self._sound_effect.isPlaying()


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
