import ctypes
import ctypes.wintypes


def get_monitor_info():
    monitors = []

    class RECT(ctypes.Structure):
        _fields_ = [
            ('left', ctypes.c_long),
            ('top', ctypes.c_long),
            ('right', ctypes.c_long),
            ('bottom', ctypes.c_long)
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_ulong),
            ('rcMonitor', RECT),
            ('rcWork', RECT),
            ('dwFlags', ctypes.c_ulong)
        ]

        def __init__(self):
            self.cbSize = ctypes.sizeof(MONITORINFO)

    def callback(hMonitor, _hdcMonitor, _lprcMonitor, _dwData):
        monitor_info = MONITORINFO()
        ctypes.windll.user32.GetMonitorInfoW(
            hMonitor, ctypes.byref(monitor_info))

        is_primary = "Yes" if monitor_info.dwFlags & 1 else "No"

        monitors.append({
            "Handle": str(hMonitor),
            "IsPrimary": is_primary,
            "Left": monitor_info.rcMonitor.left,
            "Top": monitor_info.rcMonitor.top,
            "Right": monitor_info.rcMonitor.right,
            "Bottom": monitor_info.rcMonitor.bottom
        })
        return True

    callback_func = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_void_p)
    ctypes.windll.user32.EnumDisplayMonitors(
        None, None, callback_func(callback), 0)

    return monitors

# m_info = get_monitor_info()
# for i, monitor in enumerate(m_info, 1):
#     print(f"Monitor Number: {i}")
#     print(f"Handle: {monitor['Handle']}")
#     print(f"Is Primary: {monitor['IsPrimary']}")
#     print(f"Position: Left={monitor['Left']}, Top={monitor['Top']}, Right={monitor['Right']}, Bottom={monitor['Bottom']}")
#     print(f"Resolution: {monitor['Right'] - monitor['Left']}x{monitor['Bottom'] - monitor['Top']}")
#     print()
