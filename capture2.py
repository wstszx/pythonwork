import ctypes
import pygetwindow as gw
from PIL import Image

# WinAPI 常量和函数定义 (简化版)
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
PW_CLIENTONLY = 1 # 有时可能需要0来包含边框  (实际使用中，3 (PW_RENDERFULLCONTENT) 可能对现代应用更好)

WINDOW_TITLE = "XStreaming - default"
OUTPUT_FILENAME = "printwindow_capture.png"

try:
    target_windows = gw.getWindowsWithTitle(WINDOW_TITLE)
    if not target_windows:
        print(f"错误：找不到窗口 '{WINDOW_TITLE}'")
    else:
        target_window_gw = target_windows[0]
        hwnd = target_window_gw._hWnd # 获取窗口句柄 (HWND)
        print(f"找到窗口: {target_window_gw.title}, HWND: {hwnd}")

        if target_window_gw.isMinimized:
            print("窗口已最小化，PrintWindow可能只捕获到图标或标题栏。")
        
        # 获取窗口客户区矩形
        client_rect = ctypes.wintypes.RECT()
        get_client_rect_result = user32.GetClientRect(hwnd, ctypes.byref(client_rect))
        
        if not get_client_rect_result:
            raise Exception(f"无法获取窗口客户区矩形 (HWND: {hwnd})")

        # client_rect 现在包含了客户区的坐标 (相对于窗口左上角)
        # client_rect.left 和 client_rect.top 通常是 0
        # client_rect.right 是客户区宽度
        # client_rect.bottom 是客户区高度
        client_width = client_rect.right - client_rect.left
        client_height = client_rect.bottom - client_rect.top
        
        # 我们通常需要整个窗口的尺寸，而不仅仅是客户区，来进行截图
        # GetWindowRect 获取的是屏幕坐标
        window_rect_struct = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(window_rect_struct))
        width = window_rect_struct.right - window_rect_struct.left
        height = window_rect_struct.bottom - window_rect_struct.top

        if width <= 0 or height <= 0:
            print("窗口尺寸无效。")
        else:
            print(f"窗口实际尺寸 (GetWindowRect): {width}x{height}")
            print(f"客户区尺寸 (GetClientRect): {client_width}x{client_height}")

            # 对于PrintWindow，我们通常使用客户区的尺寸，或者整个窗口尺寸
            # 如果PW_CLIENTONLY, 使用客户区尺寸
            capture_width = client_width if PW_CLIENTONLY else width
            capture_height = client_height if PW_CLIENTONLY else height
            
            if capture_width <= 0 or capture_height <= 0:
                print(f"用于捕获的尺寸无效 (宽: {capture_width}, 高: {capture_height})")
            else:
                print(f"将要捕获的尺寸: {capture_width}x{capture_height}")
                mem_dc = gdi32.CreateCompatibleDC(None)
                if not mem_dc:
                    raise Exception("无法创建内存DC")

                bitmap = gdi32.CreateCompatibleBitmap(user32.GetDC(None), capture_width, capture_height)
                if not bitmap:
                    gdi32.DeleteDC(mem_dc)
                    raise Exception("无法创建兼容位图")

                gdi32.SelectObject(mem_dc, bitmap)

                # PW_RENDERFULLCONTENT (3) 尝试获取所有内容，包括DWM渲染的。
                # PW_CLIENTONLY (1) 只客户区。
                # 0 (默认) 包含边框和标题栏，但可能不包括DWM内容。
                # 对于现代应用，可以尝试 PW_CLIENTONLY 或者 3
                print_window_flags = PW_CLIENTONLY # 或尝试 0 或 3
                # print_window_flags = 3 # PW_RENDERFULLCONTENT

                result = user32.PrintWindow(hwnd, mem_dc, print_window_flags)
                print(f"PrintWindow result (flags={print_window_flags}): {result}") # 1表示成功

                if result == 1:
                    class BITMAPINFOHEADER(ctypes.Structure):
                        _fields_ = [
                            ("biSize", ctypes.c_uint32),
                            ("biWidth", ctypes.c_int),
                            ("biHeight", ctypes.c_int),
                            ("biPlanes", ctypes.c_ushort),
                            ("biBitCount", ctypes.c_ushort),
                            ("biCompression", ctypes.c_uint32),
                            ("biSizeImage", ctypes.c_uint32),
                            ("biXPelsPerMeter", ctypes.c_int),
                            ("biYPelsPerMeter", ctypes.c_int),
                            ("biClrUsed", ctypes.c_uint32),
                            ("biClrImportant", ctypes.c_uint32),
                        ]

                    bmi = BITMAPINFOHEADER()
                    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                    bmi.biWidth = capture_width
                    bmi.biHeight = -capture_height # 负数表示顶向下位图
                    bmi.biPlanes = 1
                    bmi.biBitCount = 24 # 通常RGB是24位
                    bmi.biCompression = 0 # BI_RGB

                    # 计算图像缓冲区大小 (每行字节数必须是4的倍数)
                    stride = (capture_width * bmi.biBitCount + 31) // 32 * 4
                    buffer_size = stride * capture_height
                    image_buffer = ctypes.create_string_buffer(buffer_size)
                    
                    get_di_bits_result = gdi32.GetDIBits(
                        mem_dc, bitmap, 0, capture_height,
                        image_buffer, ctypes.byref(bmi), 0 # DIB_RGB_COLORS = 0
                    )

                    if get_di_bits_result:
                        img = Image.frombuffer("RGB", (capture_width, capture_height), image_buffer, "raw", "BGR", stride, 1)
                        # 注意 Image.frombuffer 的 stride 参数是每行的字节数
                        img.save(OUTPUT_FILENAME)
                        print(f"PrintWindow 截图已保存为 {OUTPUT_FILENAME}")
                    else:
                        print(f"GetDIBits 失败。错误代码: {ctypes.GetLastError()}")
                else:
                    print(f"PrintWindow 失败。错误代码: {ctypes.GetLastError()}")
                    print("这可能意味着目标窗口不支持此操作，或者内容受保护/DWM渲染的内容无法通过此方式获取。")

                gdi32.DeleteObject(bitmap)
                gdi32.DeleteDC(mem_dc)

except Exception as e:
    print(f"发生错误: {e}")