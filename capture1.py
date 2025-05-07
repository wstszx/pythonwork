from windows_capture import WindowsCapture, Frame, InternalCaptureControl

# 创建捕获对象，指定窗口标题
capture = WindowsCapture(window_name="XStreaming - default")  # 替换为目标窗口的标题

@capture.event
def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
    print("新帧到达")
    frame.save_as_image("capture.png")  # 保存截图
    capture_control.stop()  # 停止捕获

@capture.event
def on_closed():
    print("捕获会话已关闭")

capture.start()
