# -*- coding: utf-8 -*-
from ctypes import windll, create_unicode_buffer, byref, GetLastError, wintypes
import sys
import time
import win32con
import win32gui
import ctypes # 导入 ctypes 模块以使用 cast 和 POINTER
import traceback # 导入 traceback 模块以打印详细错误信息

# --- Windows API 初始化 ---
user32 = windll.user32
PostMessageW = user32.PostMessageW
MapVirtualKeyW = user32.MapVirtualKeyW
VkKeyScanA = user32.VkKeyScanA
SendMessageW = user32.SendMessageW
FindWindowW = user32.FindWindowW
IsWindow = user32.IsWindow
EnumChildWindows = user32.EnumChildWindows
GetClassNameW = user32.GetClassNameW
SetForegroundWindow = user32.SetForegroundWindow # 用于激活窗口
GetShellWindow = user32.GetShellWindow
IsUserAnAdmin = windll.shell32.IsUserAnAdmin
ShellExecuteW = windll.shell32.ShellExecuteW

# --- Windows 消息常量 ---
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E

# --- 虚拟键码表 (根据需要扩展) ---
VK_CODE = {
    # 字母键
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
    'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
    'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
    'Z': 0x5A,

    # 功能键
    'ENTER': win32con.VK_RETURN, # 使用 VK_RETURN 更通用
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
    """检查并尝试获取管理员权限"""
    try:
        is_admin = IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        print("脚本需要管理员权限运行，正在尝试提权...")
        try:
            result = ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            if result <= 32: # 根据 ShellExecuteW 文档，小于等于 32 表示错误
                 print(f"提权失败，错误码: {result}")
                 sys.exit(1)
            else:
                 print("提权请求已发送，请在弹出的UAC窗口确认。脚本将退出，请重新运行提权后的脚本。")
                 sys.exit(0) # 退出当前实例，等待用户确认UAC后手动运行
        except Exception as e:
            print(f"提权过程中发生错误: {e}")
            sys.exit(1)
    print("已以管理员权限运行。")
    return True


def get_window_handle(window_title: str) -> int:
    """根据窗口标题获取主窗口句柄"""
    handle = FindWindowW(None, window_title)
    if not handle or not IsWindow(handle):
        raise ValueError(f"未找到标题为 '{window_title}' 的窗口，请确保程序已运行且标题匹配。")
    return handle

def _enum_child_windows_callback(hwnd, lParam):
    """枚举子窗口的回调函数"""
    target_class_name = "Chrome_RenderWidgetHostHWND"
    buffer = create_unicode_buffer(100)
    GetClassNameW(hwnd, buffer, 100)
    # print(f"  找到子控件:句柄={hwnd}, 类名='{buffer.value}'") # 调试用
    if buffer.value == target_class_name:
        # 找到了目标控件，将其存储在 lParam 指向的列表中
        ctypes.cast(lParam, ctypes.POINTER(wintypes.HWND))[0] = hwnd
        return False # 停止枚举
    return True # 继续枚举

def find_target_control(parent_handle: int) -> int:
    """在父窗口中查找目标渲染控件 (Chrome_RenderWidgetHostHWND)"""
    target_hwnd = wintypes.HWND(0) # 用于存储找到的句柄
    EnumChildWindows(parent_handle,
                     ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(_enum_child_windows_callback),
                     ctypes.byref(target_hwnd))

    if target_hwnd.value and IsWindow(target_hwnd.value):
        print(f"找到目标渲染控件: {target_hwnd.value}")
        return target_hwnd.value
    else:
        print("警告：未找到 'Chrome_RenderWidgetHostHWND' 控件，将尝试向主窗口发送按键。")
        return parent_handle # 如果找不到，回退到主窗口句柄

def get_control_text(handle: int) -> str:
    """获取控件文本内容 (可能对渲染控件无效)"""
    try:
        text_length = SendMessageW(handle, WM_GETTEXTLENGTH, 0, 0)
        if text_length == 0:
            return ""
        buffer = create_unicode_buffer(text_length + 1)
        SendMessageW(handle, WM_GETTEXT, text_length + 1, byref(buffer))
        return buffer.value
    except Exception as e:
        print(f"获取控件文本时出错: {e}")
        return "[获取文本失败]"


def get_virtual_keycode(key: str) -> int:
    """获取虚拟键码（支持字符和名称）"""
    if len(key) == 1 and key.isprintable():
        # 对于可打印字符，使用 VkKeyScanA 获取基础 VK Code
        result = VkKeyScanA(ord(key))
        vk_code = result & 0xFF
        # shift_state = (result >> 8) & 0xFF # 可以获取 Shift, Ctrl, Alt 状态，暂时不用
        if vk_code == 0xFFFFFFFF: # Windows API 返回 -1 表示失败
             raise ValueError(f"无法获取字符 '{key}' 的虚拟键码")
        return vk_code
    key_upper = key.upper()
    if key_upper in VK_CODE:
        return VK_CODE[key_upper]
    raise ValueError(f"不支持的按键名称: {key}")

def _send_key(handle: int, vk_code: int, is_extended: bool = False):
    """内部函数：发送单个按键的按下和抬起事件"""
    scan_code = MapVirtualKeyW(vk_code, 0) # MAPVK_VK_TO_VSC

    # --- 按下 ---
    # lparam for WM_KEYDOWN:
    # Bit 0-15: Repeat count (usually 1)
    # Bit 16-23: Scan code
    # Bit 24: Extended key flag (1 for keys like ALT, CTRL, arrow keys, etc.)
    # Bit 29: Context code (usually 0)
    # Bit 30: Previous key state (0 for key down)
    # Bit 31: Transition state (0 for key down)
    lparam_down = 1 | (scan_code << 16)
    if is_extended:
        lparam_down |= (1 << 24)
    PostMessageW(handle, WM_KEYDOWN, vk_code, lparam_down)
    # print(f"Sent KEYDOWN: VK={hex(vk_code)}, Scan={hex(scan_code)}, LParam={hex(lparam_down)}") # 调试

    time.sleep(0.05) # 短暂延迟模拟按键

    # --- 抬起 ---
    # lparam for WM_KEYUP:
    # Bit 0-15: Repeat count (usually 1)
    # Bit 16-23: Scan code
    # Bit 24: Extended key flag
    # Bit 30: Previous key state (must be 1 for key up)
    # Bit 31: Transition state (must be 1 for key up)
    lparam_up = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)
    if is_extended:
        lparam_up |= (1 << 24)
    PostMessageW(handle, WM_KEYUP, vk_code, lparam_up)
    # print(f"Sent KEYUP:   VK={hex(vk_code)}, Scan={hex(scan_code)}, LParam={hex(lparam_up)}") # 调试

def is_extended_key(vk_code: int) -> bool:
    """判断是否为扩展键"""
    # 根据常见的扩展键列表判断
    extended_keys = {
        win32con.VK_RCONTROL, win32con.VK_RMENU, # Right Ctrl/Alt
        win32con.VK_INSERT, win32con.VK_DELETE, win32con.VK_HOME, win32con.VK_END,
        win32con.VK_PRIOR, win32con.VK_NEXT, # Page Up/Down
        win32con.VK_UP, win32con.VK_DOWN, win32con.VK_LEFT, win32con.VK_RIGHT,
        win32con.VK_NUMLOCK, win32con.VK_CANCEL, # Break key
        win32con.VK_SNAPSHOT, # Print Screen
        win32con.VK_DIVIDE, # Numpad /
    }
    # 注意：左右 Shift/Ctrl/Alt 通常由 MapVirtualKey 或其他方式区分，
    # 但为了 PostMessage 的 lparam，有时需要明确指定。
    # 这里简化处理，将通用的 Ctrl/Alt 也视为可能需要扩展标志。
    if vk_code in extended_keys or vk_code in [win32con.VK_CONTROL, win32con.VK_MENU]:
         return True
    return False


def send_single_key(handle: int, key: str):
    """向指定句柄发送单个按键事件（按下和抬起）"""
    vk_code = get_virtual_keycode(key)
    extended = is_extended_key(vk_code)
    _send_key(handle, vk_code, extended)
    print(f"已发送按键: {key}")

def send_combination_key(handle: int, modifier_key: str, key: str):
    """向指定句柄发送组合键事件 (例如 Ctrl+A)"""
    mod_vk = get_virtual_keycode(modifier_key)
    key_vk = get_virtual_keycode(key)
    mod_extended = is_extended_key(mod_vk)
    key_extended = is_extended_key(key_vk)

    mod_scan = MapVirtualKeyW(mod_vk, 0)
    key_scan = MapVirtualKeyW(key_vk, 0)

    # 1. 按下修饰键 (Ctrl)
    lparam_mod_down = 1 | (mod_scan << 16)
    if mod_extended: lparam_mod_down |= (1 << 24)
    PostMessageW(handle, WM_KEYDOWN, mod_vk, lparam_mod_down)
    print(f"按下修饰键: {modifier_key}")
    time.sleep(0.05)

    # 2. 按下主键 (A)
    lparam_key_down = 1 | (key_scan << 16)
    if key_extended: lparam_key_down |= (1 << 24)
    PostMessageW(handle, WM_KEYDOWN, key_vk, lparam_key_down)
    print(f"按下主键: {key}")
    time.sleep(0.05)

    # 3. 抬起主键 (A)
    lparam_key_up = 1 | (key_scan << 16) | (1 << 30) | (1 << 31)
    if key_extended: lparam_key_up |= (1 << 24)
    PostMessageW(handle, WM_KEYUP, key_vk, lparam_key_up)
    print(f"抬起主键: {key}")
    time.sleep(0.05)

    # 4. 抬起修饰键 (Ctrl)
    lparam_mod_up = 1 | (mod_scan << 16) | (1 << 30) | (1 << 31)
    if mod_extended: lparam_mod_up |= (1 << 24)
    PostMessageW(handle, WM_KEYUP, mod_vk, lparam_mod_up)
    print(f"抬起修饰键: {modifier_key}")
    print(f"已发送组合键: {modifier_key}+{key}")


import pytesseract
import win32gui
import win32con
import win32ui
from ctypes import windll
from PIL import Image
import time

# 配置Tesseract路径（Windows需指定安装位置）
pytesseract.pytesseract.tesseract_cmd = r'C:\pythonwork\Tesseract\tesseract.exe'


def ocr_recognize(image, lang='chi_sim'):
    # 图像预处理（可选）
    gray_img = image.convert('L')  # 转为灰度图
    # 文字识别
    text = pytesseract.image_to_string(gray_img, lang=lang)
    return text




# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    # 0. 检查并获取管理员权限
    check_admin_privilege()

    # 1. 定义目标窗口标题 (请根据实际情况修改)
    #    你需要启动你的 XStreamingDesktop 应用，并查看其确切的窗口标题
    #    可能是 "XStreaming - default", "XStreaming - <实例名>", 或其他
    window_title = "XStreaming - 111" # <--- 修改这里

    try:


        print(f"正在查找窗口: '{window_title}'...")
        # 2. 获取主窗口句柄
        main_handle = get_window_handle(window_title)
        print(f"找到主窗口句柄: {main_handle}")
        try:
            SetForegroundWindow(main_handle)
            time.sleep(0.5) # 等待窗口激活
        except Exception as e:
            print(f"尝试激活窗口时出错 (可能无需担心): {e}")

        if main_handle != 0:
            from capture import capture_window
            img = capture_window(main_handle)
            img.show()
            result = ocr_recognize(img)
            print("识别结果：\n", result)
        else:
            print("未找到目标窗口")
        # 尝试将窗口置于前台 (可选，但有时有助于确保接收消息)



        # 3. 查找接收输入的子控件 (Electron 渲染区域)
        target_control_handle = find_target_control(main_handle)
        # print(f"目标控件文本: {get_control_text(target_control_handle)}") # 调试用

        print("\n--- 开始发送按键 ---")
        # 等待一下，确保窗口完全准备好
        time.sleep(1)

        # 4. 发送单个按键示例
        send_single_key(target_control_handle, 'ENTER')
        time.sleep(0.5) # 按键之间稍作停顿

        send_single_key(target_control_handle, 'TAB')
        time.sleep(0.5)

        send_single_key(target_control_handle, 'A')
        time.sleep(0.5)
        send_single_key(target_control_handle, 'B')
        time.sleep(0.5)
        send_single_key(target_control_handle, 'C')
        time.sleep(0.5)

        # 5. 发送组合键示例 (Ctrl+A)
        send_combination_key(target_control_handle, 'CTRL', 'A')
        time.sleep(0.5)

        # 6. 发送其他组合键示例 (Alt+F4 - 关闭窗口，请谨慎使用!)
        # send_combination_key(target_control_handle, 'ALT', 'F4')

        print("\n--- 按键发送完成 ---")

    except ValueError as ve:
        print(f"错误: {ve}")
        print("请检查窗口标题是否正确，以及程序是否已运行。")
        import traceback
        traceback.print_exc() # 打印详细错误堆栈
        sys.exit(1)
    except Exception as e:
        print(f"操作过程中发生未预料的错误: {e}")
        import traceback
        traceback.print_exc() # 打印详细错误堆栈
        sys.exit(1)

    input("按任意键退出...") # 添加这一行让窗口暂停