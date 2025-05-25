import os
import sys
import json
import tempfile
import subprocess

# 复制server.py中的launch_feedback_ui函数
def launch_feedback_ui(summary: str, predefinedOptions: list[str] | None = None) -> dict[str, str]:
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

        print(f"使用的feedback_ui.py路径: {feedback_ui_path}")
        print(f"Python解释器路径: {sys.executable}")

        # Run feedback_ui.py as a separate process with visible output
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt", summary,
            "--output-file", output_file,
            "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else ""
        ]
        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )

        # 打印所有输出以便调试
        print(f"返回代码: {result.returncode}")
        print(f"标准输出: {result.stdout.decode('utf-8', errors='ignore')}")
        print(f"错误输出: {result.stderr.decode('utf-8', errors='ignore')}")

        if result.returncode != 0:
            raise Exception(f"Failed to launch feedback UI: {result.returncode}")

        # Read the result from the temporary file if it exists
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                try:
                    result_data = json.load(f)
                    print(f"读取到的结果: {result_data}")
                    os.unlink(output_file)
                    return result_data
                except json.JSONDecodeError:
                    print("结果文件解析失败")
                    os.unlink(output_file)
                    return {"interactive_feedback": "解析失败"}
        else:
            print("结果文件不存在")
            return {"interactive_feedback": "文件不存在"}
    except Exception as e:
        print(f"发生错误: {e}")
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

if __name__ == "__main__":
    print("启动测试...")
    result = launch_feedback_ui("测试服务器加载", ["选项1", "选项2"])
    print(f"测试完成，结果: {result}") 