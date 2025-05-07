import ctypes
import ctypes.wintypes as wintypes
from time import sleep

# 定义Windows API
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# 常量定义
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
MAPVK_VK_TO_VSC = 0

# 虚拟键码表
VK_CODE = {
    'ctrl': 0x11,
    'shift': 0x10,
    'alt': 0x12,
    'n': 0x4E,
    # 可根据需要扩展更多键位
}

class WindowController:
    def __init__(self):
        self._current_thread_id = kernel32.GetCurrentThreadId()
    
    def find_window(self, title: str) -> int:
        """查找窗口句柄（支持模糊匹配）"""
        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_callback(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                buffer = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, buffer, 256)
                # if title.lower() in buffer.value.lower():
                #     ctypes.windll.kernel32.SetLastError(0)
                #     ctypes.pythonapi.PyCapsule_SetPointer(lparam, hwnd)
                #     return False
            return True
        
        hwnd = wintypes.HWND()
        user32.EnumWindows(enum_callback, ctypes.py_object(hwnd))
        return hwnd.value if hwnd.value else 0



        
    def _send_key(self, hwnd: int, vk_code: int, is_down: bool):
        """发送单个按键事件"""
        scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
        lparam = (scan_code << 16) | (0x1 if is_down else 0xC0000001)
        msg_type = WM_KEYDOWN if is_down else WM_KEYUP
        
        if not user32.PostMessageW(hwnd, msg_type, vk_code, lparam):
            raise ctypes.WinError(ctypes.get_last_error())

    def send_char(self, hwnd: int, char: str):
        """发送单个字符"""
        vk_scan = user32.VkKeyScanW(ord(char))
        if vk_scan == -1:
            raise ValueError(f"无效字符: {char}")
        
        vk_code = vk_scan & 0xFF
        self._send_key(hwnd, vk_code, True)
        sleep(0.02)
        self._send_key(hwnd, vk_code, False)
        sleep(0.02)

    def send_text(self, hwnd: int, text: str):
        """发送文本"""
        for char in text:
            self.send_char(hwnd, char)
            sleep(0.05)

    def send_shortcut(self, hwnd: int, *keys: str):
        """发送组合快捷键（如 'ctrl', 'n'）"""
        # 按下修饰键
        modifiers = []
        for key in keys[:-1]:
            key = key.lower()
            if key not in ['ctrl', 'alt', 'shift']:
                continue
            vk = VK_CODE[key]
            self._send_key(hwnd, vk, True)
            modifiers.append(vk)
            sleep(0.05)

        # 发送主键
        main_key = keys[-1].lower()
        self.send_char(hwnd, main_key.upper() if len(main_key) == 1 else main_key)
        sleep(0.1)

        # 释放修饰键
        for vk in reversed(modifiers):
            self._send_key(hwnd, vk, False)
            sleep(0.05)

    def _attach_input(self, hwnd: int):
        """附加到目标窗口的输入队列"""
        target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        if not user32.AttachThreadInput(self._current_thread_id, target_thread_id, True):
            raise ctypes.WinError(ctypes.get_last_error())

    def _detach_input(self, hwnd: int):
        """分离输入队列"""
        target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        user32.AttachThreadInput(self._current_thread_id, target_thread_id, False)

    def safe_send(self, hwnd: int, func, *args):
        """安全发送包装器"""
        try:
            self._attach_input(hwnd)
            return func(hwnd, *args)
        finally:
            self._detach_input(hwnd)

# 使用示例
if __name__ == "__main__":
    controller = WindowController()
    
    # 查找窗口（示例：记事本）
    hwnd = controller.find_window("aa - 记事本")
    if not hwnd:
        print("窗口未找到")
        exit()

    # 发送Ctrl+N新建
    controller.safe_send(hwnd, controller.send_shortcut, 'ctrl', 'n')
    
    # 发送文本
    controller.safe_send(hwnd, controller.send_text, "Hello World!")
    
    # 发送Alt+F4关闭窗口
    controller.safe_send(hwnd, controller.send_shortcut, 'alt', 'f4')