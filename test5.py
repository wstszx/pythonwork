from ctypes import windll,create_string_buffer,byref,create_unicode_buffer,GetLastError
from ctypes.wintypes import HWND,WPARAM, LPARAM

import string,win32con,win32process,win32gui
import time

PostMessageW = windll.user32.PostMessageW
MapVirtualKeyW = windll.user32.MapVirtualKeyW
VkKeyScanA = windll.user32.VkKeyScanA
SendMessage = windll.user32.SendMessageW

WM_KEYDOWN = 0x100
WM_KEYUP = 0x101
WM_GETTEXT = 0x000D


#提高进程完整性
import ctypes
from ctypes import wintypes

# 常量定义
TOKEN_ALL_ACCESS = 0x000F0000 | 0x01FF
TokenIntegrityLevel = 25  # 对应 TOKEN_INFORMATION_CLASS 中的枚举值

# 定义 Windows 结构体
class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Sid", ctypes.c_void_p),
        ("Attributes", wintypes.DWORD),
    ]

class TOKEN_MANDATORY_LABEL(ctypes.Structure):
    _fields_ = [
        ("Label", SID_AND_ATTRIBUTES),
    ]

# 函数声明
OpenProcessToken = ctypes.windll.advapi32.OpenProcessToken
OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
OpenProcessToken.restype = wintypes.BOOL

SetTokenInformation = ctypes.windll.advapi32.SetTokenInformation
SetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
SetTokenInformation.restype = wintypes.BOOL

ConvertStringSidToSid = ctypes.windll.advapi32.ConvertStringSidToSidW
ConvertStringSidToSid.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]
ConvertStringSidToSid.restype = wintypes.BOOL

LocalFree = ctypes.windll.kernel32.LocalFree
LocalFree.argtypes = [ctypes.c_void_p]
LocalFree.restype = ctypes.c_void_p

def set_high_integrity():
    # 获取当前进程令牌
    hToken = wintypes.HANDLE()
    if not OpenProcessToken(
        ctypes.windll.kernel32.GetCurrentProcess(),
        TOKEN_ALL_ACCESS,
        ctypes.byref(hToken)
    ):
        raise ctypes.WinError()

    # 转换 SID 字符串为指针
    sid_str = u"S-1-16-12288"  # 高完整性级别 SID
    pSid = ctypes.c_void_p()
    if not ConvertStringSidToSid(sid_str, ctypes.byref(pSid)):
        raise ctypes.WinError()

    # 构造 TOKEN_MANDATORY_LABEL 结构体
    mandatory_label = TOKEN_MANDATORY_LABEL()
    mandatory_label.Label.Sid = pSid
    mandatory_label.Label.Attributes = 0x00000020  # SE_GROUP_INTEGRITY

    # 设置令牌信息
    token_info = ctypes.byref(mandatory_label)
    token_info_size = ctypes.sizeof(TOKEN_MANDATORY_LABEL)

    if not SetTokenInformation(
        hToken,
        TokenIntegrityLevel,
        token_info,
        token_info_size
    ):
        LocalFree(pSid)
        raise ctypes.WinError()

    # 释放资源
    LocalFree(pSid)
    return True


# https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
VkCode1 = {
    "enter" :0x0D,
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
    "rmenu":  0XA5,
    "A":0x41,
}


# 定义常用虚拟键码
VK_CODE = {
    'A': 0x41,
    'ENTER': win32con.VK_RETURN,
    'LEFT': win32con.VK_LEFT,
    'CTRL': win32con.VK_CONTROL,
    '1': 0x31,
    # 添加更多按键...
}

# 需要设置扩展标志的键集合
EXTENDED_KEYS = {
    win32con.VK_UP, win32con.VK_DOWN,
    win32con.VK_LEFT, win32con.VK_RIGHT,
    win32con.VK_HOME, win32con.VK_END,
    win32con.VK_INSERT, win32con.VK_DELETE,
    win32con.VK_RCONTROL, win32con.VK_RMENU
}

def get_window_text(hwnd):
    # 先获取文本长度
    length = windll.user32.SendMessageW(hwnd, 0x000E, 0, 0)  # WM_GETTEXTLENGTH
    
    # 创建缓冲区
    buffer = create_unicode_buffer(length + 1)
    
    # 获取文本
    SendMessage(hwnd, WM_GETTEXT, length + 1, byref(buffer))
    return buffer.value


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
        return VkCode1[key]


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
    lParam_down = 0x1 | (scan_code << 16) | (0x1 << 30)
    
    PostMessageW(handle, WM_KEYDOWN, wparam, lparam)


def key_up(handle: HWND, key: str):
    """放开指定按键

    Args:
        handle (HWND): 窗口句柄
        key (str): 按键名
    """
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)# 0表示从虚拟键码转扫描码
    # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keyup
    wparam = vk_code
    lparam = (scan_code << 16) | 0XC0000001
    lParam_up = (0x1 | (scan_code << 16) | (0x1 << 30) | (0x1 << 31))  # 释放状态
    PostMessageW(handle, WM_KEYUP, wparam, lparam)

def send_keypress(handle, vk_code):
    key_down(handle, vk_code)  # 需实现WM_KEYDOWN发送
    key_up(handle, vk_code)

def send_key(hwnd, key_name, with_char=True):
    """
    向指定窗口发送完整按键事件
    :param hwnd: 目标窗口句柄
    :param key_name: 按键名称（支持预定义键名或直接虚拟键码）
    :param with_char: 是否发送WM_CHAR消息
    """
    # 获取虚拟键码
    vk_code = VK_CODE.get(key_name.upper(), key_name)
    if isinstance(vk_code, str):
        vk_code = ord(key_name.upper())
    
    # 获取目标窗口线程信息
    target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
    current_thread_id = windll.kernel32.GetCurrentThreadId()
    
    # 绑定线程输入队列
    windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
    
    try:
        # 获取扫描码和扩展标志
        scan_code = windll.user32.MapVirtualKeyW(vk_code, 0)  # MAPVK_VK_TO_VSC
        is_extended = vk_code in EXTENDED_KEYS
        ext_flag = 0x01000000 if is_extended else 0
        
        # 构造消息参数
        lparam_down = 0x0001 | (scan_code << 16) | ext_flag
        lparam_up = lparam_down | 0xC0000000
        
        # 发送按键按下事件
        windll.user32.PostMessageW(hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
        
        # 发送字符消息（如果需要）
        if with_char and 0x20 <= vk_code <= 0x7E:
            char = chr(vk_code)
            windll.user32.PostMessageW(hwnd, win32con.WM_CHAR, ord(char), lparam_down)
        
        # 发送按键释放事件
        windll.user32.PostMessageW(hwnd, win32con.WM_KEYUP, vk_code, lparam_up)
        
        # 强制刷新消息队列
        windll.user32.PostMessageW(hwnd, win32con.WM_NULL, 0, 0)
        windll.user32.MsgWaitForMultipleObjects(0, 0, 0, 50, 0xFF)
        
    finally:
        # 解除线程绑定
        windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)

def get_window_text(hwnd):
    # 获取文本长度
    text_len = windll.user32.SendMessageW(hwnd, 0x000E, 0, 0)  # WM_GETTEXTLENGTH
    
    # 分配缓冲区
    buffer = create_unicode_buffer(text_len + 1)
    
    # 获取文本内容
    windll.user32.SendMessageW(
        hwnd, 
        0x000D,  # WM_GETTEXT
        text_len + 1, 
        byref(buffer)
    )
    return buffer.value






if __name__ == "__main__":

    # 需要和目标窗口同一权限，游戏窗口通常是管理员权限
    import sys

    if not windll.shell32.IsUserAnAdmin():
        # 不是管理员就提权
        windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1)
        

    try:
        set_high_integrity()
        print("成功设置高完整性级别")
    except Exception as e:
        print(f"错误：{e}")


    import win32gui

    def callback(hwnd, controls):
        controls.append(hwnd)

    hwnd = win32gui.FindWindow(None, "xbox远程游玩") # 根据窗口标题获取句柄
    controls = []
    win32gui.EnumChildWindows(hwnd, callback, controls)

    for control in controls:
        print(control)

    handle = windll.user32.FindWindowW(None, "xbox远程游玩")#Dead Cells  FLUTTERVIEW
    # 关闭
    #SendMessage(handle, 0x0010, 0, 0)#关闭
    #获取标题
    a=get_window_text(handle)
    # 检查
    is_valid = windll.user32.IsWindow(HWND(handle))
    print("窗口句柄有效" if is_valid else "窗口句柄无效")


    send_key(handle, 'ENTER', with_char=False)
    
    # 发送方向键
    send_key(handle, 'LEFT', with_char=False)

    key_down(handle, 'enter')
    time.sleep(0.1)
    key_up(handle, 'enter')
