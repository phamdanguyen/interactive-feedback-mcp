import os
import sys
import json
import tempfile
import subprocess

def test_uv_run():
    """测试uv run启动feedback_ui.py"""
    print("开始测试uv run...")
    
    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")
    
    print(f"使用的feedback_ui.py路径: {feedback_ui_path}")
    
    # 启动命令
    cmd = [
        "uv", "run",
        feedback_ui_path,
        "--prompt", "测试uv run加载",
        "--predefined-options", "选项A|||选项B|||选项C"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 运行命令
    result = subprocess.run(
        cmd,
        check=False,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        close_fds=True
    )
    
    # 打印结果
    print(f"返回代码: {result.returncode}")
    print(f"标准输出: {result.stdout.decode('utf-8', errors='ignore')}")
    print(f"错误输出: {result.stderr.decode('utf-8', errors='ignore')}")
    
    print("测试完成")

if __name__ == "__main__":
    test_uv_run() 