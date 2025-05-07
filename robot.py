from ctypes import windll, create_unicode_buffer, byref, GetLastError
from ctypes.wintypes import HWND, WPARAM, LPARAM
import sys
import time
import win32con
import win32gui

# 初始化Windows API函数
user32 = windll.user32
PostMessageW = user32.PostMessageW
MapVirtualKeyW = user32.MapVirtualKeyW
VkKeyScanA = user32.VkKeyScanA
SendMessageW = user32.SendMessageW

# 定义Windows消息常量
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E

# 虚拟键码表（扩展版）
VK_CODE = {
    # 字母键
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
    'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
    'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
    'Z': 0x5A,
    
    # 功能键
    'ENTER': 0x0D,
    'BACKSPACE': win32con.VK_BACK,
    'TAB': win32con.VK_TAB,
    'SHIFT': win32con.VK_SHIFT,
    'CTRL': win32con.VK_CONTROL,
    'ALT': win32con.VK_MENU,
    'ESC': win32con.VK_ESCAPE,
    'SPACE': win32con.VK_SPACE,
    
    # 方向键
    'LEFT': win32con.VK_LEFT,
    'UP': win32con.VK_UP,
    'RIGHT': win32con.VK_RIGHT,
    'DOWN': win32con.VK_DOWN,
    
    # 数字键（主键盘）
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33,
    '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37,
    '8': 0x38, '9': 0x39,
    
    # 其他常用键
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73,
    'F5': 0x74, 'F6': 0x75, 'F7': 0x76, 'F8': 0x77,
    'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
}

def check_admin_privilege():
    """检查并获取管理员权限"""
    try:
        if not user32.GetShellWindow():
            return False
        if not windll.shell32.IsUserAnAdmin():
            windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, __file__, None, 1)
            sys.exit()
        return True
    except Exception as e:
        print(f"提权失败: {str(e)}")
        return False

def get_window_handle(window_title: str):
    """根据窗口标题获取主窗口句柄"""
    handle = user32.FindWindowW(None, window_title)
    if not handle or not user32.IsWindow(HWND(handle)):
        raise ValueError(f"未找到标题为'{window_title}'的窗口")
    return handle

def callback(hwnd, controls):
    controls.append(hwnd)

def get_child_controls(parent_handle: int):
    """获取指定窗口的所有子控件句柄"""
    controls = []
    win32gui.EnumChildWindows(parent_handle, callback, controls)
    return controls

def get_control_text(handle: int):
    """获取控件文本内容"""
    text_length = SendMessageW(HWND(handle), WM_GETTEXTLENGTH, 0, 0)
    buffer = create_unicode_buffer(text_length + 1)
    SendMessageW(HWND(handle), WM_GETTEXT, text_length + 1, byref(buffer))
    return buffer.value

def get_virtual_keycode(key: str):
    """获取虚拟键码（支持字符和名称）"""
    if len(key) == 1 and key.isprintable():
        return VkKeyScanA(ord(key)) & 0xFF
    key_upper = key.upper()
    if key_upper in VK_CODE:
        return VK_CODE[key_upper]
    raise ValueError(f"不支持的按键: {key}")


def send_key_event(handle: int, key: str, press_time: float = 0.1):
    """向指定控件发送按键事件"""
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)
    
    # 发送按下事件
    lparam_down = (scan_code << 16) | 1
    PostMessageW(HWND(handle), WM_KEYDOWN, WPARAM(vk_code), LPARAM(lparam_down))
    
    # 保持按下状态
    time.sleep(press_time)
    
    # 发送释放事件
    lparam_up = (scan_code << 16) | 0xC0000001
    PostMessageW(HWND(handle), WM_KEYUP, WPARAM(vk_code), LPARAM(lparam_up))


def get_real_handle(name):
    #查找测试接受键盘消息的控件
    main_window = get_window_handle(name)
    print(f"主窗口句柄: {main_window}")
    
    # 获取所有子控件
    controls = get_child_controls(main_window)
    print(f"找到 {len(controls)} 个子控件{controls}")
    target_control = main_window
    print(f"目标控件文本: {get_control_text(target_control)}")
    return target_control
# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    # 检查管理员权限
    check_admin_privilege()

    try:
        # 查找主窗口
        target_control = get_real_handle("XStreaming - 111")#XStreaming - 111

        # 发送回车键
        send_key_event(target_control, 'ENTER')
        print("已发送回车键")

        # 发送组合键示例（例如Ctrl+A）
        send_key_event(target_control, 'CTRL')
        send_key_event(target_control, 'A')
        # 发送组合键示例（例如Ctrl+A）

        
    except Exception as e:
        print(f"操作失败: {str(e)}")
        sys.exit(1)