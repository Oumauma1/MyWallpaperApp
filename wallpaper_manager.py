import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32api

class WallpaperManager:
    def __init__(self):
        self._workerw = None

    def _init_workerw(self):
        """寻找并初始化 WorkerW 窗口，这是放置壁纸的关键位置"""
        progman = win32gui.FindWindow("Progman", None)
        
        # 发送 0x052C 消息给 Progman，生成 WorkerW
        # 这一步至关重要，它分离了桌面图标层和背景层
        win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)

        workerw_list = []
        def enum_windows_proc(hwnd, lParam):
            shell_dll_defview = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
            if shell_dll_defview:
                # 找到了包含图标的 WorkerW，它的兄弟窗口就是我们要找的背景层
                workerw_list.append(win32gui.FindWindowEx(0, hwnd, "WorkerW", None))
            return True

        win32gui.EnumWindows(enum_windows_proc, 0)
        
        # 通常是列表中的最后一个，但也可能直接遍历找到
        if workerw_list:
            self._workerw = workerw_list[0]
        else:
            # 备用方案：再次枚举寻找没有 SHELLDLL_DefView 子窗口的 WorkerW
            def find_workerw(hwnd, lParam):
                 if win32gui.GetClassName(hwnd) == "WorkerW":
                     if not win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None):
                         workerw_list.append(hwnd)
                 return True
            win32gui.EnumWindows(find_workerw, 0)
            if workerw_list:
                self._workerw = workerw_list[-1] # 通常最新的一个是正确的

    def set_window_as_wallpaper(self, window_handle):
        """将指定的窗口句柄设置为壁纸"""
        if not self._workerw:
            self._init_workerw()
        
        if self._workerw:
            # 获取屏幕尺寸
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            # 先调整窗口大小和位置，再设置父窗口
            # 这样可以确保窗口在正确的位置和大小显示，避免父窗口设置后调整大小时的视觉闪烁
            win32gui.MoveWindow(window_handle, 0, 0, screen_width, screen_height, True)
            
            # 设置窗口样式以确保正确嵌入
            style = win32gui.GetWindowLong(window_handle, win32con.GWL_STYLE)
            style = style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME
            win32gui.SetWindowLong(window_handle, win32con.GWL_STYLE, style)
            
            # 将目标窗口设为 WorkerW 的子窗口
            win32gui.SetParent(window_handle, self._workerw)
            
            # 再次确保位置和大小正确
            win32gui.MoveWindow(window_handle, 0, 0, screen_width, screen_height, True)

    def is_foreground_maximized(self):
        """检测当前前台窗口是否最大化"""
        foreground_window = win32gui.GetForegroundWindow()
        if not foreground_window:
            return False
        
        # 获取窗口放置状态
        placement = win32gui.GetWindowPlacement(foreground_window)
        # placement[1] 是 showCmd，SW_SHOWMAXIMIZED 值为 3
        if placement[1] == win32con.SW_SHOWMAXIMIZED:
            # 排除桌面本身和我们自己的程序
            class_name = win32gui.GetClassName(foreground_window)
            if class_name not in ["Progman", "WorkerW"]:
                return True
        return False
