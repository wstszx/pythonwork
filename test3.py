import ctypes
import win32con
import win32gui
import win32process

def send_background_key(hwnd, vk_code, char=None):
    """
    向指定窗口发送后台键盘事件
    :param hwnd: 目标窗口句柄
    :param vk_code: 虚拟键码（如win32con.VK_A）
    :param char: 可选字符（用于发送WM_CHAR）
    """
    # 验证窗口有效性
    if not ctypes.windll.user32.IsWindow(hwnd):
        raise ValueError("无效窗口句柄")

    # 获取线程ID
    target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

    # 绑定输入队列
    if not ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True):
        raise ctypes.WinError()

    try:
        # 定义扩展键集合
        extended_keys = {
            win32con.VK_UP, win32con.VK_DOWN, win32con.VK_LEFT, win32con.VK_RIGHT,
            win32con.VK_HOME, win32con.VK_END, win32con.VK_PRIOR, win32con.VK_NEXT,
            win32con.VK_INSERT, win32con.VK_DELETE, win32con.VK_RCONTROL,
            win32con.VK_RMENU, win32con.VK_RWIN
        }

        # 获取扫描码并判断扩展键
        scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)  # MAPVK_VK_TO_VSC
        is_extended = vk_code in extended_keys

        # 构造lParam参数
        repeat_count = 0x0001
        ext_flag = 0x01000000 if is_extended else 0x00000000
        context_code = 0x00000000  # ALT未按下
        transition_state = 0x00000000  # 按键按下

        # WM_KEYDOWN的lParam
        lparam_down = (repeat_count |
                      (scan_code << 16) |
                      ext_flag |
                      context_code |
                      transition_state)

        # WM_KEYUP的lParam（设置第31位）
        lparam_up = lparam_down | 0xC0000000

        # 发送键盘消息序列
        ctypes.windll.user32.SendMessageW(hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
        
        # 发送字符消息（可选）
        if char is not None:
            char_code = ord(char)
            ctypes.windll.user32.SendMessageW(hwnd, win32con.WM_CHAR, char_code, lparam_down)
        
        ctypes.windll.user32.SendMessageW(hwnd, win32con.WM_KEYUP, vk_code, lparam_up)

    finally:
        # 解除线程绑定
        ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)


import sys
# 检查管理员权限
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

# 获取记事本窗口句柄
notepad_hwnd = ctypes.windll.user32.FindWindowW(None, "FreeReNamer")
#notepad_hwnd = win32gui.FindWindow("Dead Cells", None)

# 发送字母'A'
#send_background_key(notepad_hwnd, win32con.VK_A, 'A')

# 发送回车键
# 添加消息队列刷新（重要！）
ctypes.windll.user32.PostMessageW(notepad_hwnd, win32con.WM_NULL, 0, 0)
ctypes.windll.user32.MsgWaitForMultipleObjects(0, 0, 0, 50, 0xFF)
send_background_key(notepad_hwnd, win32con.VK_SPACE)