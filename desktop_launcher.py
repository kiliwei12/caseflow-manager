"""CaseFlow desktop launcher used by PyInstaller builds."""
from pathlib import Path
import os
import platform
import socket
import sys
import threading
import webbrowser


def user_data_dir():
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "CaseFlow"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "CaseFlow"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "CaseFlow"


def available_port(start=8080, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("没有可用的本地端口，请关闭其他 CaseFlow 实例后重试。")


def main():
    data_dir = user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CASEFLOW_DATA_DIR"] = str(data_dir)
    os.environ["CASEFLOW_DESKTOP_MODE"] = "1"
    os.environ.pop("CASEFLOW_DEMO_MODE", None)

    from app import app, init_db
    from waitress import serve

    init_db()
    port = available_port()
    url = f"http://127.0.0.1:{port}"
    if os.environ.get("CASEFLOW_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    serve(app, host="127.0.0.1", port=port, threads=6, clear_untrusted_proxy_headers=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_dir = user_data_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "startup-error.log").write_text(str(exc), encoding="utf-8")
        if getattr(sys, "frozen", False):
            try:
                import tkinter.messagebox
                tkinter.messagebox.showerror("CaseFlow 启动失败", f"{exc}\n\n错误日志：{log_dir / 'startup-error.log'}")
            except Exception:
                pass
        raise
