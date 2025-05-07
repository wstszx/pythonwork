import uiautomation as auto
import time
import win32api
import win32con

def test_chrome_background_control():
    # 定位目标控件（根据提供的属性）
    chrome_doc = auto.Control(
        ClassName="Chrome_RenderWidgetHostHWND",
        AutomationId="501888",
        NativeWindowHandle=0x30A88  # 替换为实际句柄（注意 0x30A88 是十六进制）
    )

    if not chrome_doc.Exists():
        raise Exception("未找到目标 Chrome 渲染控件！")

    # 确保控件获取焦点（可选）
    chrome_doc.SetFocus()
    time.sleep(0.5)

    # === 场景1：发送导航快捷键 ===
    # 发送 F5 刷新页面（通过 uiautomation）
    chrome_doc.SendKeys("{F5}", waitTime=1)
    print("已发送 F5 刷新指令")
    time.sleep(2)

    # === 场景2：通过 Win32 API 发送后台组合键 ===
    def send_ctrl_r(hwnd):
        # 按下 Ctrl
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
        # 按下 R
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_R, 0)
        # 释放 R
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_R, 0)
        # 释放 Ctrl
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)

    # 获取窗口句柄
    hwnd = chrome_doc.NativeWindowHandle
    send_ctrl_r(hwnd)
    print("已发送 Ctrl+R 刷新指令")
    time.sleep(2)

    # === 场景3：模拟方向键操作 ===
    # 发送向下箭头键（浏览页面滚动）
    chrome_doc.SendKeys("{Down}", waitTime=0.2, interval=0.1)
    chrome_doc.SendKeys("{Down}", waitTime=0.2)
    print("已发送两次向下箭头键")

    # === 场景4：尝试激活输入（需实际可编辑区域存在）===
    # 查找子输入控件（可能需要更精准的定位条件）
    input_area = chrome_doc.EditControl(searchDepth=2)
    if input_area.Exists():
        input_area.SendKeys("Test Input")
    else:
        print("未找到可编辑区域，跳过输入测试")

if __name__ == "__main__":
    test_chrome_background_control()