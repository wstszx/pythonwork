import win32gui
import win32con
import win32ui
import win32api
from ctypes import windll
from PIL import Image
import time

def get_window_handle(window_title):
    """通过窗口标题获取句柄（支持模糊匹配）"""
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd: return hwnd
    
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_title.lower() in title.lower():
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else 0

def capture_window(hwnd):
    """后台截图（支持最小化窗口）"""
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    x, y = win32gui.ClientToScreen(hwnd, (left, top))
    
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, right-left, bottom-top)
    saveDC.SelectObject(saveBitMap)
    
    windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
    
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )
    
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    
    return img

def send_key(hwnd, key, activate_window=False, use_unicode=False):
    """
    向指定窗口发送按键
    :param hwnd: 窗口句柄
    :param key: 可以是虚拟键码（如win32con.VK_RETURN）或字符（如'A'）
    :param activate_window: 是否激活窗口到前台
    :param use_unicode: 是否使用Unicode方式发送字符（WM_CHAR消息）
    """

    if activate_window:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.2)

    if isinstance(key, str) and len(key) == 1:
        if use_unicode:
            # 使用WM_CHAR发送Unicode字符
            win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(key), 0)
        else:
            # 解析虚拟键码和修饰键
            vk_key = win32api.VkKeyScan(key)
            if vk_key == -1:
                raise ValueError(f"无效的字符: {key}")
            
            modifiers = (vk_key >> 8) & 0xFF
            vk_code = vk_key & 0xFF
            
            # 处理修饰键
            modifier_keys = [
                (win32con.VK_SHIFT, 0x1),
                (win32con.VK_CONTROL, 0x2),
                (win32con.VK_MENU, 0x4)  # Alt键
            ]
            
            # 按下修饰键
            for vk, flag in modifier_keys:
                if modifiers & flag:
                    win32api.keybd_event(vk, 0, 0, 0)
            
            # 发送按键
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            win32api.keybd_event(vk_code, scan_code, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
            
            # 释放修饰键
            for vk, flag in reversed(modifier_keys):
                if modifiers & flag:
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
    else:
        # 直接发送虚拟键码
        scan_code = win32api.MapVirtualKey(key, 0)
        win32api.keybd_event(key, scan_code, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(key, scan_code, win32con.KEYEVENTF_KEYUP, 0)

def send_virtual_key_message(hwnd, vk_code):
    """
    通过窗口消息发送虚拟按键（后台模式，不一定所有程序都支持）
    :param hwnd: 窗口句柄
    :param vk_code: 虚拟键码
    """
    scan_code = win32api.MapVirtualKey(vk_code, 0)
    lparam_down = 0x00000001 | (scan_code << 16)
    lparam_up = 0xC0000001 | (scan_code << 16)
    
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lparam_up)

if __name__ == "__main__":
    window_title = "新建文本文档 - 记事本"
    
    hwnd = get_window_handle(window_title)
    if not hwnd:
        print("窗口未找到")
        exit()

    # 后台截图测试
    img = capture_window(hwnd)
    img.save("hidden_capture.png")

    # 发送按键测试（使用前台模式）

    # send_key(hwnd, win32con.VK_RETURN, activate_window=False)  # 发送回车键
    # time.sleep(1)
    # send_key(hwnd, 'A', activate_window=False)  # 发送大写字母A

# 发送后台消息测试（可能不适用于所有程序）
    send_virtual_key_message(hwnd, win32con.VK_RETURN)  # 发送消息