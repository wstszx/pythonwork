# import uiautomation as auto

# # 获取微信主窗口
# wechat_window = auto.WindowControl(searchDepth=1, ClassName='WeWorkWindow')

# # 激活微信窗口
# wechat_window.SetFocus()

# # 遍历并打印所有控件
# def print_control_info(control, depth=0):
#     # 打印控件信息
#     print(' ' * depth * 4 + f'控件类型: {control.ControlTypeName}, 控件名称: {control.Name}')
#     # 递归遍历子控件
#     for child in control.GetChildren():
#         print_control_info(child, depth + 1)


# # 开始遍历
# print_control_info(wechat_window)

# import pyautogui

# def bring_to_front_max(window_name):
#     try:
#         # 查找窗口标题
#         window_list = pyautogui.getWindowsWithTitle(window_name)

#         # 检查是否找到了窗口
#         if window_list:
#             window = window_list[0]
#             # 将窗口切换到前台并最大化
#             window.minimize() 
#             window.restore()  # 恢复窗口到前台
#             window.maximize()  # 最大化窗口
#         else:
#             print(f"未找到标题为 '{window_name}' 的窗口。")
#     except Exception as e:
#         print(f"发生错误：{e}")

# bring_to_front_max('微信')

import uiautomation as auto

def print_controls(control, indent=0):
    try:
        # 打印当前控件信息
        print(' ' * indent + f"ControlType: {control.ControlTypeName}")
        print(' ' * indent + f"ClassName: {control.ClassName}")
        print(' ' * indent + f"Name: {control.Name}")
        print(' ' * indent + f"AutomationId: {control.AutomationId}")
        print(' ' * indent + f"BoundingRectangle: {control.BoundingRectangle}")
        print(' ' * indent + "-" * 50)
        
        # 递归打印子控件
        for child in control.GetChildren():
            print_controls(child, indent + 4)
            
    except Exception as e:
        print(' ' * indent + f"Error reading control: {str(e)}")

# 获取主窗口
wechat_window = auto.WindowControl(searchDepth=1, ClassName='Edit')#WeChatMainWndForPC   WeWorkWindow

# 激活窗口
wechat_window.SetFocus()

# 打印所有控件信息（从主窗口开始遍历）
print("开始打印企业微信控件结构...")
print_controls(wechat_window)
print("控件结构打印完成")
