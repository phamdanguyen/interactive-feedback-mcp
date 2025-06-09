"""
终端管理器
Terminal Manager

统一管理多种终端的检测、配置和启动。
Unified management for detection, configuration and launching of multiple terminals.
"""

import os
import sys
import subprocess
from typing import Dict, List, Optional

from .constants import (
    TERMINAL_POWERSHELL,
    TERMINAL_GITBASH,
    TERMINAL_CMD,
    DEFAULT_TERMINAL_TYPE,
    TERMINAL_TYPES,
)


class TerminalManager:
    """终端管理器，负责检测和管理系统中的终端程序"""

    def __init__(self):
        self.available_terminals: Dict[str, str] = {}
        self.custom_paths: Dict[str, str] = {}
        self.detect_terminals()

    def detect_terminals(self):
        """检测系统中可用的终端"""
        # 检测 PowerShell
        powershell_path = self._detect_powershell()
        if powershell_path:
            self.available_terminals[TERMINAL_POWERSHELL] = powershell_path

        # 检测 Git Bash
        gitbash_path = self._detect_git_bash()
        if gitbash_path:
            self.available_terminals[TERMINAL_GITBASH] = gitbash_path

        # 检测 Command Prompt
        cmd_path = self._detect_cmd()
        if cmd_path:
            self.available_terminals[TERMINAL_CMD] = cmd_path

    def _detect_powershell(self) -> str:
        """检测 PowerShell 路径"""
        if os.name == "nt":  # Windows
            candidates = [
                # PowerShell 7+ 常见安装路径
                r"C:\Program Files\PowerShell\7\pwsh.exe",
                r"C:\Program Files\PowerShell\6\pwsh.exe",
                # Windows PowerShell 5.1
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            ]

            # 检查绝对路径
            for candidate in candidates:
                if os.path.isfile(candidate):
                    return candidate

            # 通过 PATH 查找
            for cmd in ["pwsh.exe", "powershell.exe"]:
                try:
                    result = subprocess.run(
                        ["where", cmd], capture_output=True, text=True, shell=True
                    )
                    if result.returncode == 0:
                        return result.stdout.strip().split("\n")[0]
                except Exception:
                    continue

        return ""

    def _detect_git_bash(self) -> str:
        """检测 Git Bash 路径"""
        if os.name == "nt":  # Windows
            candidates = [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
            ]

            # 检查绝对路径
            for candidate in candidates:
                if os.path.isfile(candidate):
                    return candidate

            # 尝试从注册表获取 Git 路径
            git_registry_path = self._get_git_path_from_registry()
            if git_registry_path and os.path.isfile(git_registry_path):
                return git_registry_path

            # 通过 PATH 查找
            try:
                result = subprocess.run(
                    ["where", "bash"], capture_output=True, text=True, shell=True
                )
                if result.returncode == 0:
                    # 检查是否是 Git Bash
                    bash_path = result.stdout.strip().split("\n")[0]
                    if "git" in bash_path.lower():
                        return bash_path
            except Exception:
                pass

        return ""

    def _get_git_path_from_registry(self) -> str:
        """从注册表获取 Git 安装路径"""
        try:
            import winreg

            # 尝试不同的注册表位置
            registry_paths = [
                r"SOFTWARE\GitForWindows",
                r"SOFTWARE\WOW6432Node\GitForWindows",
            ]

            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    winreg.CloseKey(key)
                    bash_path = os.path.join(install_path, "bin", "bash.exe")
                    if os.path.isfile(bash_path):
                        return bash_path
                except Exception:
                    continue
        except ImportError:
            # winreg 不可用（非 Windows 系统）
            pass
        except Exception:
            pass

        return ""

    def _detect_cmd(self) -> str:
        """检测 Command Prompt 路径"""
        if os.name == "nt":  # Windows
            cmd_path = r"C:\Windows\System32\cmd.exe"
            if os.path.isfile(cmd_path):
                return cmd_path

            # 备用检测
            try:
                result = subprocess.run(
                    ["where", "cmd"], capture_output=True, text=True, shell=True
                )
                if result.returncode == 0:
                    return result.stdout.strip().split("\n")[0]
            except Exception:
                pass

        return ""

    def get_terminal_command(self, terminal_type: str) -> str:
        """获取指定类型终端的启动命令"""
        # 优先使用自定义路径
        if terminal_type in self.custom_paths:
            custom_path = self.custom_paths[terminal_type]
            if custom_path and os.path.isfile(custom_path):
                return custom_path

        # 使用检测到的路径
        return self.available_terminals.get(terminal_type, "")

    def set_custom_path(self, terminal_type: str, path: str):
        """设置终端的自定义路径"""
        if path and os.path.isfile(path):
            self.custom_paths[terminal_type] = path
        elif terminal_type in self.custom_paths:
            del self.custom_paths[terminal_type]

    def validate_terminal_path(self, path: str) -> bool:
        """验证终端路径是否有效"""
        return bool(path and os.path.isfile(path))

    def get_terminal_args(self, terminal_type: str) -> List[str]:
        """获取不同终端的启动参数"""
        args_map = {
            TERMINAL_POWERSHELL: ["-NoLogo", "-NoExit"],
            TERMINAL_GITBASH: ["--login", "-i"],
            TERMINAL_CMD: ["/k"],
        }
        return args_map.get(terminal_type, [])

    def get_terminal_prompt(self, terminal_type: str) -> str:
        """获取不同终端的提示符"""
        prompt_map = {
            TERMINAL_POWERSHELL: "PS>",
            TERMINAL_GITBASH: "$",
            TERMINAL_CMD: ">",
        }
        return prompt_map.get(terminal_type, ">")

    def get_available_terminals(self) -> Dict[str, str]:
        """获取所有可用的终端"""
        return self.available_terminals.copy()

    def is_terminal_available(self, terminal_type: str) -> bool:
        """检查指定终端是否可用"""
        return (
            terminal_type in self.available_terminals
            or terminal_type in self.custom_paths
        )

    def get_terminal_info(self, terminal_type: str) -> Optional[Dict]:
        """获取终端信息"""
        if terminal_type in TERMINAL_TYPES:
            info = TERMINAL_TYPES[terminal_type].copy()
            info["available"] = self.is_terminal_available(terminal_type)
            info["path"] = self.get_terminal_command(terminal_type)
            return info
        return None

    def get_working_directory_command(
        self, terminal_type: str, working_dir: str
    ) -> str:
        """获取设置工作目录的命令"""
        if terminal_type == TERMINAL_POWERSHELL:
            return f'Set-Location "{working_dir}"'
        elif terminal_type == TERMINAL_GITBASH:
            return f'cd "{working_dir}"'
        elif terminal_type == TERMINAL_CMD:
            return f'cd /d "{working_dir}"'
        else:
            return f'cd "{working_dir}"'


# 全局终端管理器实例
_terminal_manager = None


def get_terminal_manager() -> TerminalManager:
    """获取全局终端管理器实例"""
    global _terminal_manager
    if _terminal_manager is None:
        _terminal_manager = TerminalManager()
    return _terminal_manager
