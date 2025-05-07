from ctypes import windll
from ctypes.wintypes import HWND
import string
import time
from ctypes import *


import win32con,win32gui,win32process
# 定义常量
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_RIGHT = 0x27  # 方向键右的虚拟键码

PostMessageW = windll.user32.PostMessageW
MapVirtualKeyW = windll.user32.MapVirtualKeyW
VkKeyScanA = windll.user32.VkKeyScanA

WM_KEYDOWN = 0x100
WM_KEYUP = 0x101

# https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
VkCode = {
    "enter":  0x0D,
    "back":  0x08,
    "tab":  0x09,
    "return":  0x0D,
    "shift":  0x10,
    "control":  0x11,
    "menu":  0x12,
    "pause":  0x13,
    "capital":  0x14,
    "escape":  0x1B,
    "space":  0x20,
    "end":  0x23,
    "home":  0x24,
    "left":  0x25,
    "up":  0x26,
    "right":  0x27,
    "down":  0x28,
    "print":  0x2A,
    "snapshot":  0x2C,
    "insert":  0x2D,
    "delete":  0x2E,
    "lwin":  0x5B,
    "rwin":  0x5C,
    "numpad0":  0x60,
    "numpad1":  0x61,
    "numpad2":  0x62,
    "numpad3":  0x63,
    "numpad4":  0x64,
    "numpad5":  0x65,
    "numpad6":  0x66,
    "numpad7":  0x67,
    "numpad8":  0x68,
    "numpad9":  0x69,
    "multiply":  0x6A,
    "add":  0x6B,
    "separator":  0x6C,
    "subtract":  0x6D,
    "decimal":  0x6E,
    "divide":  0x6F,
    "f1":  0x70,
    "f2":  0x71,
    "f3":  0x72,
    "f4":  0x73,
    "f5":  0x74,
    "f6":  0x75,
    "f7":  0x76,
    "f8":  0x77,
    "f9":  0x78,
    "f10":  0x79,
    "f11":  0x7A,
    "f12":  0x7B,
    "numlock":  0x90,
    "scroll":  0x91,
    "lshift":  0xA0,
    "rshift":  0xA1,
    "lcontrol":  0xA2,
    "rcontrol":  0xA3,
    "lmenu":  0xA4,
    "rmenu":  0XA5
}


def get_virtual_keycode(key: str):
    """根据按键名获取虚拟按键码

    Args:
        key (str): 按键名

    Returns:
        int: 虚拟按键码
    """
    if len(key) == 1 and key in string.printable:
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscana
        return VkKeyScanA(ord(key)) & 0xff
    else:
        return VkCode[key]


def key_down(handle: HWND, key: str):
    """按下指定按键

    Args:
        handle (HWND): 窗口句柄
        key (str): 按键名
    """
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)
    # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keydown
    wparam = vk_code
    lparam = (scan_code << 16) | 1
    PostMessageW(handle, WM_KEYDOWN, wparam, lparam)


def key_up(handle: HWND, key: str):
    """放开指定按键

    Args:
        handle (HWND): 窗口句柄
        key (str): 按键名
    """
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)
    # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keyup
    wparam = vk_code
    lparam = (scan_code << 16) | 0XC0000001
    PostMessageW(handle, WM_KEYUP, wparam, lparam)


def send_char(hwnd, char):
    PostMessageW(hwnd, WM_CHAR, ord(char), 0)

def send_vk_key(hwnd, vk_code):
    scan_code = MapVirtualKeyW(vk_code, 0)  # MAPVK_VK_TO_VSC
    lparam_down = 0x0001 | (scan_code << 16)
    lparam_up = lparam_down | (0x1 << 31)
    
    PostMessageW(hwnd, WM_KEYDOWN, vk_code, lparam_down)
    PostMessageW(hwnd, WM_KEYUP, vk_code, lparam_up)


def send_vk_key2(hwnd, vk_code):
    extended_keys = {win32con.VK_RCONTROL, win32con.VK_RMENU, win32con.VK_RSHIFT, 
                    win32con.VK_LEFT, win32con.VK_RIGHT, win32con.VK_UP, win32con.VK_DOWN}
    is_extended = vk_code in extended_keys

    scan_code = windll.user32.MapVirtualKeyW(vk_code, 0)  # MAPVK_VK_TO_VSC
    lparam_down = 0x0001 | (scan_code << 16)
    if is_extended:
        lparam_down |= 0x01000000  # 扩展键标志位
    lparam_up = lparam_down | 0xC0000000  # 释放标志

    # 确保窗口在前台
    #win32gui.SetForegroundWindow(hwnd)

    # 发送消息
    windll.user32.PostMessageW(hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
    windll.user32.PostMessageW(hwnd, win32con.WM_KEYUP, vk_code, lparam_up)

def send_background_input(hwnd, vk_code):
    # 获取目标线程ID（关键步骤）
    target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
    current_thread_id = windll.kernel32.GetCurrentThreadId()

    # 绑定线程输入队列（必须管理员权限）
    if not windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True):
        raise WinError()

    try:
        # 创建硬件级输入事件（绕过焦点限制）
        class KEYBDINPUT(Structure):
            _fields_ = [
                ("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", POINTER(c_ulong))
            ]

        class INPUT(Structure):
            _fields_ = [("type", c_ulong),
                        ("ki", KEYBDINPUT),
                        ("pad", c_ubyte * 8)]

        # 使用扫描码模式（更底层）
        scan_code = windll.user32.MapVirtualKeyW(vk_code, 0)
        flag = 0x0008  # KEYEVENTF_SCANCODE

        # 构造按下和释放事件
        inputs = (INPUT * 2)()
        inputs[0].type = win32con.INPUT_KEYBOARD
        inputs[0].ki = KEYBDINPUT(0, scan_code, flag, 0, None)
        
        inputs[1].type = win32con.INPUT_KEYBOARD
        inputs[1].ki = KEYBDINPUT(0, scan_code, flag | win32con.KEYEVENTF_KEYUP, 0, None)

        # 发送定向输入（关键参数）

        windll.user32.SendInput(2, byref(inputs), sizeof(INPUT))
    finally:
        windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
def send_background_input2(hwnd, vk_code):
    # 强制类型转换
    try:
        vk_code = int(vk_code)
    except ValueError:
        raise TypeError("vk_code必须是整数类型的虚拟键码")

    # 获取目标窗口线程ID
    _, target_pid = win32process.GetWindowThreadProcessId(hwnd)
    current_pid = windll.kernel32.GetCurrentThreadId()

    # 附加到目标线程输入队列
    windll.user32.AttachThreadInput(current_pid, target_pid, True)

    try:
        # 使用SendInput模拟硬件输入
        class KEYBDINPUT(Structure):
            _fields_ = [("wVk", c_ushort),
                        ("wScan", c_ushort),
                        ("dwFlags", c_ulong),
                        ("time", c_ulong),
                        ("dwExtraInfo", POINTER(c_ulong))]

        class INPUT(Structure):
            _fields_ = [("type", c_ulong),
                        ("ki", KEYBDINPUT),
                        ("pad", c_ubyte * 8)]

        inputs = INPUT * 2
        keyboard_input = inputs()

        # 按下事件
        keyboard_input[0].type = 1  # INPUT_KEYBOARD
        keyboard_input[0].ki.wVk = c_ushort(vk_code)  # 显式类型声明
        keyboard_input[0].ki.dwFlags = 0x0008  # KEYEVENTF_SCANCODE
        keyboard_input[0].ki.wScan = windll.user32.MapVirtualKeyW(vk_code, 0)

        # 释放事件
        keyboard_input[1].type = 1
        keyboard_input[1].ki.wVk = c_ushort(vk_code)
        keyboard_input[1].ki.dwFlags = 0x0008 | 0x0002  # KEYEVENTF_KEYUP
        keyboard_input[1].ki.wScan = keyboard_input[0].ki.wScan

        # 发送输入
        windll.user32.SendInput(2, byref(keyboard_input), sizeof(INPUT))
    finally:
        # 解除线程附加
        windll.user32.AttachThreadInput(current_pid, target_pid, False)


if __name__ == "__main__":
    # 需要和目标窗口同一权限，游戏窗口通常是管理员权限
    import sys
    if not windll.shell32.IsUserAnAdmin():
        # 不是管理员就提权
        windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1)

    handle = windll.user32.FindWindowW(None, "xbox远程游玩")
    #检查名字
    p = create_string_buffer(256)
    windll.user32.GetWindowTextW(handle,byref(p),256) # 获取窗口标题
    title = str(p.raw,encoding='utf-16').strip('\x00') # 解码


    # send_char(handle, '1')
    send_vk_key2(handle,0x0D)




    send_background_input(handle,0x0D)
    # 控制角色向前移动两秒
    key_down(handle, 'enter')
    time.sleep(0.5)
    key_up(handle, 'enter')