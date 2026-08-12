import pygetwindow as gw


def get_active_window():

    try:
        window = gw.getActiveWindow()

        if window is None:
            return None

        return {
            "title": window.title,
            "left": window.left,
            "top": window.top,
            "width": window.width,
            "height": window.height,
        }

    except Exception:
        return None