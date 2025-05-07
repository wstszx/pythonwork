import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import time
import ctypes # Needed for IsProcessDPIAware

# Optional: Make the script DPI aware, can sometimes help with scaling issues
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except AttributeError: # Windows 7 or older
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass # Could not set DPI awareness

def capture_admin_window(window_title, filename="screenshot.png"):
    """
    截图指定标题的窗口（需要管理员权限运行此脚本）。

    Args:
        window_title (str): 目标窗口的精确标题。
        filename (str): 保存截图的文件名。

    Returns:
        bool: 成功返回 True，失败返回 False。
    """
    # 1. 查找窗口句柄 (HWND)
    hwnd = win32gui.FindWindow(None, window_title)
    print(f"[INFO] 查找窗口 '{window_title}', HWND: {hwnd}") # 新增日志
    if hwnd == 0:
        print(f"[ERROR] 找不到标题为 '{window_title}' 的窗口。") # 修改日志级别
        print("[INFO] 请确保窗口标题完全匹配，并且窗口已打开。") # 修改日志级别
        # Uncomment to list visible windows if needed
        # print("\n当前可见窗口标题:")
        # def winEnumHandler(hwnd_local, titles):
        #     if win32gui.IsWindowVisible(hwnd_local) and win32gui.GetWindowText(hwnd_local) != '':
        #         titles.append(win32gui.GetWindowText(hwnd_local))
        # titles = []
        # win32gui.EnumWindows(winEnumHandler, titles)
        # for t in sorted(titles):
        #      print(f"- {t}")
        return False

    # 解决最小化窗口无法截图的问题
    is_iconic = win32gui.IsIconic(hwnd) # 获取状态
    print(f"[INFO] 窗口是否最小化: {is_iconic}") # 新增日志
    if is_iconic:
        print("[INFO] 窗口已最小化，正在尝试恢复...") # 修改日志级别
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE) # 改为不激活窗口的方式恢复
        time.sleep(0.5) # 增加等待时间，确保窗口有时间绘制
        print("[INFO] 窗口已尝试恢复。") # 新增日志

    # --- 恢复尝试将窗口置于前台 ---
    # 尝试将窗口置于前台 (有时必要，但可能因权限失败)
    try:
        print("[INFO] 尝试将窗口置于前台...")
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5) # 增加等待时间，确保窗口激活并绘制
        print("[INFO] 窗口已尝试置于前台。")
    except Exception as e:
        # pywintypes.error: (5, 'SetForegroundWindow', '拒绝访问。') is common
        # even when run as admin if another higher-privilege window is active.
        print(f"[WARN] 设置前景窗口时出错 (可能是权限或焦点问题，但截图可能仍有效): {e}")
        # pass # 不需要 pass，即使失败也继续尝试截图
    # --- 结束恢复 ---


    # 2. 获取窗口位置和尺寸 (使用 GetWindowRect)
    # GetWindowRect 获取的是相对于屏幕的坐标，包括标题栏和边框
    print("[INFO] 正在获取窗口矩形 (GetWindowRect)...") # 新增日志
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bot - top
    print(f"[INFO] 窗口矩形: L={left}, T={top}, R={right}, B={bot}, W={width}, H={height}") # 新增日志

    # 获取客户区位置和尺寸 (相对于窗口左上角)
    # GetClientRect 获取的是相对于窗口客户区左上角(0,0)的坐标
    # client_left, client_top, client_right, client_bot = win32gui.GetClientRect(hwnd)
    # client_width = client_right - client_left
    # client_height = client_bot - client_top
    # print(f"Window Rect: L={left}, T={top}, R={right}, B={bot}, W={width}, H={height}")
    # print(f"Client Rect: W={client_width}, H={client_height}")


    if width <= 0 or height <= 0:
        print(f"[ERROR] 窗口尺寸无效 (宽={width}, 高={height})。窗口可能已关闭、隐藏或获取尺寸失败。") # 修改日志级别
        return False

    # 初始化资源句柄/对象
    hwndDC = None
    mfcDC = None
    saveDC = None
    saveBitMap = None
    im = None # 用于存储 PIL Image 对象
    success = False # 标记操作是否成功

    try:
        # 3. 获取窗口设备上下文 (DC)
        # GetWindowDC 获取整个窗口的 DC，包括边框和标题栏
        # GetDC 获取客户区的 DC
        # PrintWindow 理论上应该与 GetWindowDC 配合使用，但有时也需要尝试 GetDC
        # BitBlt 通常与 GetDC (客户区) 配合使用

        # --- 尝试 PrintWindow 方法 (通常更可靠，尤其对于复杂UI/硬件加速窗口) ---
        # 需要与窗口 DC (GetWindowDC) 配合
        print("[INFO] 尝试使用 PrintWindow 获取截图...") # 修改日志级别
        print("[INFO]   正在获取窗口设备上下文 (GetWindowDC)...") # 新增日志
        hwndDC = win32gui.GetWindowDC(hwnd)
        print(f"[INFO]   GetWindowDC 返回: {hwndDC}") # 新增日志
        if not hwndDC:
             print("[ERROR] 无法获取窗口设备上下文 (GetWindowDC)。") # 修改日志级别
             raise RuntimeError("无法获取 GetWindowDC")
        print("[INFO]   正在创建 MFC DC...") # 新增日志
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        print("[INFO]   正在创建兼容 DC...") # 新增日志
        saveDC = mfcDC.CreateCompatibleDC()
        print("[INFO]   正在创建兼容位图...") # 新增日志
        saveBitMap = win32ui.CreateBitmap()
        print(f"[INFO]   正在创建兼容位图 (尺寸 {width}x{height})...") # 新增日志
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height) # 使用 GetWindowRect 的尺寸
        print("[INFO]   正在将位图选入兼容 DC...") # 新增日志
        saveDC.SelectObject(saveBitMap)

        # 调用 PrintWindow
        # 参数 0: (Default) Capture window client and non-client areas.
        # 参数 1: PW_RENDERFULLCONTENT (Undocumented? Or maybe just 1 means include non-client?) - Often needed for modern UI
        # 参数 2: PW_CLIENTONLY Capture only the client area.
        # Let's try with flag 3 first (PW_CLIENTONLY | PW_RENDERFULLCONTENT)
        print("[INFO]   尝试调用 PrintWindow (flag=3)...") # 修改日志级别
        # The flag PW_RENDERFULLCONTENT (=1) might help render contents correctly, especially for layered windows.
        # PW_CLIENTONLY (=2) captures only the client area. Flag 3 combines them.
        # You might experiment with flags 0, 1, or 2 if 3 fails.
        # result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1) # Example: Try flag 1
        # result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0) # Example: Try flag 0
        # result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3) # Current: flag 3
        # 保持 PrintWindow (flag=0) 或根据上次测试结果调整
        print("[INFO]   尝试调用 PrintWindow (flag=3)...") # 改回 flag 3
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3) # 使用 flag 3
        last_error = ctypes.GetLastError()
        print(f"[INFO]   PrintWindow (flag=3) 返回: {result}, LastError: {last_error}") # 改回 flag 3


        if result == 1:
            print("[INFO] PrintWindow 成功。") # 修改日志级别
            print("[INFO]   正在获取位图信息...") # 新增日志
            bmpinfo = saveBitMap.GetInfo()
            print(f"[INFO]   位图信息: {bmpinfo}") # 新增日志
            print("[INFO]   正在获取位图数据...") # 新增日志
            bmpstr = saveBitMap.GetBitmapBits(True)
            print(f"[INFO]   位图数据长度: {len(bmpstr) if bmpstr else 0}") # 新增日志
            print("[INFO]   正在从位图数据创建 PIL Image 对象...") # 新增日志
            im = Image.frombytes('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
            print("[INFO]   PIL Image 对象已创建。") # 新增日志
            # Crop image if only client area is needed (optional, requires GetClientRect)
            # client_rect = win32gui.GetClientRect(hwnd)
            # border_width = (width - client_rect[2]) // 2
            # title_bar_height = height - client_rect[3] - border_width # Approximate
            # im = im.crop((border_width, title_bar_height, width - border_width, height - border_width))
            success = True
        else:
            print(f"[WARN] PrintWindow (flag 3) 调用失败 (返回 {result}, LastError: {last_error})。尝试使用 BitBlt...") # 改回 flag 3
            # Clean up resources specific to PrintWindow attempt before trying BitBlt
            print("[INFO]   清理 PrintWindow (flag 3) 尝试的资源...") # 改回 flag 3
            if saveDC: print("[DEBUG]     Deleting saveDC (PrintWindow)"); saveDC.DeleteDC(); saveDC = None
            if saveBitMap: print("[DEBUG]     Deleting saveBitMap (PrintWindow)"); win32gui.DeleteObject(saveBitMap.GetHandle()); saveBitMap = None
            if mfcDC: print("[DEBUG]     Deleting mfcDC (PrintWindow)"); mfcDC.DeleteDC(); mfcDC = None
            if hwndDC: print("[DEBUG]     Releasing hwndDC (PrintWindow)"); win32gui.ReleaseDC(hwnd, hwndDC); hwndDC = None
            print("[INFO]   PrintWindow 资源清理完毕。") # 新增日志


        # --- 如果 PrintWindow 失败，尝试 BitBlt 方法 (可能对旧应用有效，但对硬件加速窗口常失败) ---
        if not success:
            print("[INFO] 尝试使用 BitBlt (仅客户区) 进行截图...") # 修改日志级别

            # 需要客户区 DC (GetDC)
            print("[INFO]   正在获取客户区设备上下文 (GetDC)...") # 新增日志
            hwndDC = win32gui.GetDC(hwnd) # Note: Reusing hwndDC variable, now for GetDC
            print(f"[INFO]   GetDC 返回: {hwndDC}") # 新增日志
            if not hwndDC:
                print("[ERROR] 无法获取客户区设备上下文 (GetDC)。") # 修改日志级别
                raise RuntimeError("无法获取客户区 DC")
            print("[INFO]   正在创建 MFC DC (BitBlt)...") # 新增日志
            mfcDC = win32ui.CreateDCFromHandle(hwndDC) # Note: Reusing mfcDC

            # 获取客户区尺寸
            print("[INFO]   正在获取客户区矩形 (GetClientRect)...") # 新增日志
            left_c, top_c, right_c, bot_c = win32gui.GetClientRect(hwnd)
            width_c = right_c - left_c
            height_c = bot_c - top_c
            print(f"[INFO]   客户区矩形: L={left_c}, T={top_c}, R={right_c}, B={bot_c}, W={width_c}, H={height_c}") # 新增日志

            if width_c <= 0 or height_c <= 0:
                print(f"[ERROR] 客户区尺寸无效 (宽={width_c}, 高={height_c})。") # 修改日志级别
                raise RuntimeError("客户区尺寸无效")

            # 创建与客户区 DC 兼容的内存 DC 和位图
            print("[INFO]   正在创建兼容 DC (BitBlt)...") # 新增日志
            saveDC = mfcDC.CreateCompatibleDC() # Note: Reusing saveDC
            print("[INFO]   正在创建兼容位图 (BitBlt)...") # 新增日志
            saveBitMap = win32ui.CreateBitmap() # Note: Reusing saveBitMap
            print(f"[INFO]   正在创建兼容位图 (尺寸 {width_c}x{height_c}, BitBlt)...") # 新增日志
            saveBitMap.CreateCompatibleBitmap(mfcDC, width_c, height_c)
            print("[INFO]   正在将位图选入兼容 DC (BitBlt)...") # 新增日志
            saveDC.SelectObject(saveBitMap)

            # 执行 BitBlt (从客户区 DC 复制到内存 DC)
            print("[INFO]   尝试调用 BitBlt...") # 新增日志
            # SRCCOPY = 0x00CC0020
            try:
                result = saveDC.BitBlt((0, 0), (width_c, height_c), mfcDC, (0, 0), win32con.SRCCOPY)
                last_error = 0 # BitBlt 成功时通常不设置 LastError，但如果它抛出异常则会
                print(f"[INFO]   BitBlt 返回: {result}") # 新增日志
            except win32ui.error as e_bitblt:
                result = False # 标记为失败
                last_error = ctypes.GetLastError() # 获取错误码
                print(f"[ERROR]  BitBlt 调用时发生 win32ui 错误: {e_bitblt}, LastError: {last_error}") # 新增日志

            if result is not False: # BitBlt 成功时可能返回 None 或 True/非零值，失败时可能返回 False 或抛出异常
                 print("[INFO] BitBlt (仅客户区) 尝试成功。") # 修改日志级别
                 print("[INFO]   正在获取位图信息 (BitBlt)...") # 新增日志
                 bmpinfo = saveBitMap.GetInfo()
                 print(f"[INFO]   位图信息 (BitBlt): {bmpinfo}") # 新增日志
                 print("[INFO]   正在获取位图数据 (BitBlt)...") # 新增日志
                 bmpstr = saveBitMap.GetBitmapBits(True)
                 print(f"[INFO]   位图数据长度 (BitBlt): {len(bmpstr) if bmpstr else 0}") # 新增日志
                 print("[INFO]   正在从位图数据创建 PIL Image 对象 (BitBlt)...") # 新增日志
                 im = Image.frombytes('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
                 print("[INFO]   PIL Image 对象已创建 (BitBlt)。") # 新增日志
                 success = True
            else:
                 print(f"[ERROR] BitBlt 调用失败 (返回 {result}, LastError: {last_error})。") # 修改日志级别和内容
                 # success remains False

        # 6. 保存图像 (移到 try 块末尾，在 finally 之前)
        if success and im:
            print(f"[INFO] 尝试将图像保存到 '{filename}'...") # 新增日志
            try:
                im.save(filename)
                print(f"[SUCCESS] 截图成功，已保存为 '{filename}'") # 修改日志级别
                # --- 新增：截图成功后最小化窗口 ---
                try:
                    print(f"[INFO] 尝试最小化窗口 '{window_title}'...")
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    print(f"[INFO] 窗口 '{window_title}' 已尝试最小化。")
                except Exception as e_minimize:
                    print(f"[WARN] 最小化窗口时出错: {e_minimize}")
                # --- 结束新增 ---
            except Exception as e_save:
                print(f"[ERROR] 保存图像时失败: {e_save}") # 修改日志级别
                success = False # 保存失败，标记为不成功
        elif not success:
             print("[ERROR] 截图失败：未能通过任何方法生成有效的图像数据。") # 修改日志级别
        else: # success 为 True 但 im 为 None (理论上不可能)
             print("[ERROR] 内部错误：标记成功但图像数据为空。") # 修改日志级别
             success = False

        return success # 返回最终的成功状态

    except win32ui.error as e:
        print(f"[ERROR] 发生 win32ui 错误: {e}") # 修改日志级别
        # pywintypes.error: (1400, 'CreateCompatibleBitmap', '无效的窗口句柄。') - Window closed?
        # pywintypes.error: (87, 'BitBlt', '参数错误。') - Invalid dimensions? DC mismatch?
        return False # finally 块会处理清理
    except RuntimeError as e: # Catch specific RuntimeErrors raised above
        print(f"[ERROR] 发生运行时错误: {e}") # 修改日志级别
        return False # finally 块会处理清理
    except Exception as e:
        import traceback
        print(f"[ERROR] 发生其他意外错误: {e}") # 修改日志级别
        print("[DEBUG] Traceback:") # 新增日志
        print(traceback.format_exc()) # Print full traceback for unexpected errors
        return False # finally 块会处理清理
    finally:
        # 7. 释放所有可能已创建的资源 (非常重要)
        print("[INFO] 执行 finally 块进行资源清理...") # 修改日志级别
        if saveDC:
            print("[DEBUG]   尝试删除 saveDC...") # 新增日志
            try: saveDC.DeleteDC()
            except win32ui.error as e: print(f"[WARN] 删除 saveDC 时出错: {e}") # 修改日志级别
        if saveBitMap:
            print("[DEBUG]   尝试删除 saveBitMap...") # 新增日志
            try: win32gui.DeleteObject(saveBitMap.GetHandle())
            except win32ui.error as e: print(f"[WARN] 删除 saveBitMap 时出错: {e}") # 修改日志级别
        if mfcDC:
            print("[DEBUG]   尝试删除 mfcDC...") # 新增日志
            try: mfcDC.DeleteDC()
            except win32ui.error as e: print(f"[WARN] 删除 mfcDC 时出错: {e}") # 修改日志级别
        if hwndDC: # This handle is from either GetWindowDC or GetDC
            print("[DEBUG]   尝试释放 hwndDC...") # 新增日志
            try:
                # ReleaseDC requires the original HWND it was gotten for
                # GetWindowDC uses hwnd, GetDC also uses hwnd
                win32gui.ReleaseDC(hwnd, hwndDC)
            except win32ui.error as e: print(f"[WARN] 释放 hwndDC 时出错: {e}") # 修改日志级别
        print("[INFO] 资源清理完毕。") # 修改日志级别

# --- 使用示例 ---
if __name__ == "__main__":
    # 重要：将 "你的程序窗口标题" 替换为目标程序的精确窗口标题
    target_window_title = "XStreaming - default" # <--- 修改这里

    print(f"正在尝试截图窗口: '{target_window_title}'")
    print("请确保此 Python 脚本是以管理员权限运行的！")

    if capture_admin_window(target_window_title, "admin_screenshot_v2.png"):
        print("操作完成。")
    else:
        print("截图失败。请检查以下几点：")
        print(f"  1. 窗口标题 '{target_window_title}' 是否完全精确（包括大小写和空格）？")
        print("  2. 目标窗口当前是否已打开且可见（非最小化状态）？")
        print("  3. 此 Python 脚本是否确实以管理员权限运行？")
        print("  4. 目标程序是否使用了特殊的渲染技术（如 DirectX, OpenGL）可能与此截图方法不兼容？")
        print("  5. 目标程序是否有反截图保护？")

    # input("按 Enter 退出...")