# Interactive Feedback MCP - Cursor Direct Input
# 用于将图片和文本直接发送到Cursor对话框

import sys
import time
import pyperclip
import pyautogui
from io import BytesIO
import traceback

try:
    # 尝试导入Windows特定的剪贴板模块
    import win32clipboard
    from PIL import Image
    HAS_WIN32_CLIPBOARD = True
except ImportError:
    print("警告: win32clipboard模块导入失败，将使用备用方法", file=sys.stderr)
    HAS_WIN32_CLIPBOARD = False

def send_clipboard_image(pixmap):
    """
    将QPixmap图片放入系统剪贴板
    
    Args:
        pixmap: QPixmap图片对象
    
    Returns:
        bool: 操作是否成功
    """
    if pixmap is None or pixmap.isNull():
        print("错误: 无效的图片对象 (None 或 isNull)", file=sys.stderr)
        return False
        
    print(f"将图片放入剪贴板 (尺寸: {pixmap.width()}x{pixmap.height()})", file=sys.stderr)
    
    try:
        if HAS_WIN32_CLIPBOARD:
            # Windows实现 - 使用win32clipboard
            try:
                # 将QPixmap转换为PIL Image
                byte_array = pixmap.toImage().bits().asstring(pixmap.width() * pixmap.height() * 4)
                if not byte_array:
                    raise ValueError("无法获取图像数据")
                    
                image = Image.frombytes('RGBA', (pixmap.width(), pixmap.height()), byte_array)
                
                # 转换为BMP格式 (Windows剪贴板支持最好)
                output = BytesIO()
                image.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # 删除BMP文件头
                output.close()
                
                if not data:
                    raise ValueError("BMP转换后数据为空")
                
                # 将图像数据放入剪贴板
                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                finally:
                    win32clipboard.CloseClipboard()
                    
                print("成功使用win32clipboard设置图片剪贴板", file=sys.stderr)
            except Exception as e:
                print(f"win32clipboard方法失败，尝试备用方法: {e}", file=sys.stderr)
                # 如果win32clipboard失败，尝试Qt方法
                from PySide6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setPixmap(pixmap)
                print("成功使用Qt备用方法设置图片剪贴板", file=sys.stderr)
        else:
            # 备用方法：使用QApplication剪贴板
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            print("成功使用Qt方法设置图片剪贴板", file=sys.stderr)
        
        return True
    except Exception as e:
        print(f"向剪贴板发送图片时出错: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # 最后尝试使用最简单的方法
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setPixmap(pixmap)
            print("成功使用简化Qt方法设置图片剪贴板", file=sys.stderr)
            return True
        except Exception as e2:
            print(f"所有图片剪贴板方法都失败: {e2}", file=sys.stderr)
        return False

def save_clipboard():
    """
    保存当前剪贴板内容
    
    Returns:
        tuple: (format, data) 或 None
    """
    try:
        if HAS_WIN32_CLIPBOARD:
            try:
                win32clipboard.OpenClipboard()
                format_id = win32clipboard.GetClipboardFormat()
                if format_id:
                    data = win32clipboard.GetClipboardData(format_id)
                    win32clipboard.CloseClipboard()
                    return (format_id, data)
                win32clipboard.CloseClipboard()
            except:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
        
        # 备用方法：保存文本内容
        text = pyperclip.paste()
        return ("text", text)
    except:
        return None

def restore_clipboard(saved_content):
    """
    恢复剪贴板内容
    
    Args:
        saved_content: 由save_clipboard返回的内容
    """
    if not saved_content:
        return
    
    try:
        if HAS_WIN32_CLIPBOARD and saved_content[0] != "text":
            format_id, data = saved_content
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(format_id, data)
            win32clipboard.CloseClipboard()
        else:
            # 恢复文本内容
            pyperclip.copy(saved_content[1] if isinstance(saved_content, tuple) else saved_content)
    except:
        pass

def send_to_cursor_input(text, image_pixmaps):
    """
    将文本和图片直接发送到Cursor对话输入框
    
    Args:
        text: 要发送的文本内容
        image_pixmaps: QPixmap图片列表
    
    Returns:
        bool: 操作是否成功
    """
    print(f"准备发送到Cursor: 文本({len(text) if text else 0}字符), 图片({len(image_pixmaps)}张)", file=sys.stderr)
    
    # 保存原始剪贴板内容
    original_clipboard = save_clipboard()
    
    try:
        # 等待MCP窗口关闭/隐藏
        time.sleep(1.2)  # 增加等待时间，确保MCP窗口完全关闭
        
        # 先按ESC键确保清除当前状态
        print("首先按ESC键清除当前状态...", file=sys.stderr)
        pyautogui.press('escape')
        time.sleep(0.5)  # 等待ESC键操作生效
        
        # 使用Ctrl+L激活对话框
        print("使用Ctrl+L激活对话框...", file=sys.stderr)
        pyautogui.keyDown('ctrl')
        time.sleep(0.3)
        pyautogui.keyDown('l')  # 明确使用小写l
        time.sleep(0.2)
        pyautogui.keyUp('l')
        time.sleep(0.1)
        pyautogui.keyUp('ctrl')
        time.sleep(0.8)  # 充分等待对话框出现
        
        print("已激活Cursor对话框，准备输入内容", file=sys.stderr)
        
        # 先输入文本内容
        if text:
            print(f"发送文本内容: {text[:50]}{'...' if len(text) > 50 else ''}", file=sys.stderr)
            pyperclip.copy(text)
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.6)  # 增加等待时间
            
            # 如果同时有文本和图片，在文本后添加一个空格
            if image_pixmaps and len(image_pixmaps) > 0:
                pyautogui.press('space')
                time.sleep(0.2)
        
        # 逐个插入图片
        if image_pixmaps and len(image_pixmaps) > 0:
            for i, pixmap in enumerate(image_pixmaps):
                print(f"发送图片 {i+1}/{len(image_pixmaps)} (尺寸: {pixmap.width()}x{pixmap.height()})", file=sys.stderr)
                
                # 将图片放入剪贴板
                success = send_clipboard_image(pixmap)
                if not success:
                    print(f"警告: 图片 {i+1} 放入剪贴板失败", file=sys.stderr)
                    continue
                
                time.sleep(0.4)  # 等待剪贴板更新
                
                # 粘贴图片
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1.2)  # 增加等待时间，给足够时间处理图片
                
                # 在图片之间添加空格
                if i < len(image_pixmaps) - 1:
                    pyautogui.press('space')
                    time.sleep(0.2)
        
        # 完成所有内容添加后，按下Enter键发送
        print("所有内容已粘贴，按Enter键发送...", file=sys.stderr)
        time.sleep(0.5)  # 增加等待时间确保内容都已粘贴完成
        pyautogui.press('enter')
        
        print("发送完成", file=sys.stderr)
        
        # 恢复原始剪贴板内容
        time.sleep(0.7)  # 确保粘贴操作完成
        restore_clipboard(original_clipboard)
        
        return True
    except Exception as e:
        print(f"向Cursor输入框发送内容时出错: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # 尝试恢复剪贴板
        try:
            restore_clipboard(original_clipboard)
        except:
            pass
            
        return False

def send_to_cursor_with_sequence(text, image_pixmaps):
    """
    使用优化的按键序列将文本和图片发送到Cursor对话框
    按键序列: ESC -> 等待1s -> Ctrl+L -> 等待1s -> 注入完整内容 -> 等待1s -> Enter
    
    Args:
        text: 要发送的文本内容
        image_pixmaps: QPixmap图片列表
    
    Returns:
        bool: 操作是否成功
    """
    print(f"准备按优化序列发送到Cursor: 文本({len(text) if text else 0}字符), 图片({len(image_pixmaps)}张)", file=sys.stderr)
    
    # 保存原始剪贴板内容
    original_clipboard = save_clipboard()
    
    try:
        # 等待MCP窗口关闭/隐藏
        time.sleep(1.0)  # 增加等待时间，确保MCP窗口完全关闭
        
        # 1. 按ESC键确保清除当前状态
        print("按序列1: 按ESC键清除当前状态...", file=sys.stderr)
        pyautogui.press('escape')
        time.sleep(1.0)  # 增加等待时间到1秒
        
        # 2. 使用Ctrl+L激活对话框
        print("按序列2: 使用Ctrl+L激活对话框...", file=sys.stderr)
        pyautogui.hotkey('ctrl', 'l')  # 使用hotkey简化按键操作
        time.sleep(1.0)  # 增加等待时间到1秒
        
        print("按序列3: 准备注入所有内容(文本+图片)作为一次完整输入...", file=sys.stderr)
        
        # 3. 注入内容 - 把所有内容作为一个整体注入，不分开发送
        all_content_injected = False
        
        # 先处理文本部分
        if text:
            print(f"注入文本内容: {text[:50]}{'...' if len(text) > 50 else ''}", file=sys.stderr)
            pyperclip.copy(text)
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            all_content_injected = True
            
            # 如果同时有文本和图片，在文本后添加一个空格
            if image_pixmaps and len(image_pixmaps) > 0:
                pyautogui.press('space')
                time.sleep(0.3)
        
        # 逐个插入图片，但视为同一次输入的一部分
        if image_pixmaps and len(image_pixmaps) > 0:
            for i, pixmap in enumerate(image_pixmaps):
                print(f"注入图片 {i+1}/{len(image_pixmaps)} (尺寸: {pixmap.width()}x{pixmap.height()})", file=sys.stderr)
                
                # 将图片放入剪贴板
                success = send_clipboard_image(pixmap)
                if not success:
                    print(f"警告: 图片 {i+1} 放入剪贴板失败", file=sys.stderr)
                    continue
                
                time.sleep(0.5)  # 增加等待剪贴板更新时间
                
                # 粘贴图片
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1.0)  # 增加等待时间，确保图片完全粘贴
                all_content_injected = True
                
                # 在图片之间添加空格
                if i < len(image_pixmaps) - 1:
                    pyautogui.press('space')
                    time.sleep(0.3)
        
        # 如果没有成功注入任何内容，返回失败
        if not all_content_injected:
            print("错误: 没有注入任何内容", file=sys.stderr)
            return False
            
        # 4. 最后的等待，确保所有内容完全准备好
        time.sleep(1.0)  # 增加等待时间到1秒
        
        # 5. 按Enter键一次性发送所有内容
        print("按序列4: 按Enter键一次性发送所有内容...", file=sys.stderr)
        pyautogui.press('enter')
        
        print("优化序列发送完成", file=sys.stderr)
        
        # 恢复原始剪贴板内容
        time.sleep(0.7)
        restore_clipboard(original_clipboard)
        
        return True
    except Exception as e:
        print(f"按优化序列向Cursor输入框发送内容时出错: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # 尝试恢复剪贴板
        try:
            restore_clipboard(original_clipboard)
        except:
            pass
            
        return False

# 简单测试函数
if __name__ == "__main__":
    print("Cursor直接输入模块测试")
    print("等待3秒后将激活Cursor对话框...")
    time.sleep(3)
    
    # 测试发送文本
    print("测试发送文本到Cursor对话框...")
    test_text = "这是一个测试文本，由cursor_direct_input.py发送"
    result = send_to_cursor_input(test_text, [])
    
    if result:
        print("文本发送成功")
    else:
        print("文本发送失败")
    
    print("测试完成")