import os
import subprocess
import tkinter as tk
from tkinter import messagebox, Tk, ttk, StringVar
import psutil
import shutil
import requests
import socket
import configparser
import sys
import zipfile
import threading
import time
import pygetwindow as gw
import ctypes

CONFIG_FILE = "settings.ini"
VERSION = "0.0.3"


def load_settings():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        if "Settings" in config:
            openai_key_entry.insert(0, config.get(
                "Settings", "OPENAI_KEY", fallback=""))
            proxy_port_entry.insert(0, config.get(
                "Settings", "PROXY_PORT", fallback=""))


def save_settings():
    config = configparser.ConfigParser()
    config["Settings"] = {
        "OPENAI_KEY": openai_key_entry.get(),
        "PROXY_PORT": proxy_port_entry.get()
    }
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def on_close():
    save_settings()
    root.destroy()


def check_python_installed():
    try:
        subprocess.check_output(["python", "--version"])
        return True
    except FileNotFoundError:
        return False


def setup_environment(alter=True):
    if not check_python_installed():
        install_python()
    elif alter:
        messagebox.showinfo("信息", "Python 环境已安装")


def install_python():
    python_installer = "static\\python-3.12.6-amd64.exe"
    if os.path.exists(python_installer):
        subprocess.run([python_installer], check=True)

        subprocess.run(
            ["python", "-m", "pip", "install", "-e", "."], check=True)
        messagebox.showinfo("信息", "Python 环境已安装并设置完成")
    else:
        messagebox.showerror("错误", "找不到Python安装包")


def get_system_proxy():
    try:
        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)

        proxy_enabled, regtype = winreg.QueryValueEx(reg_key, "ProxyEnable")
        proxy_server, regtype = winreg.QueryValueEx(reg_key, "ProxyServer")

        if proxy_enabled:

            if ':' in proxy_server:
                return proxy_server.split(":")[-1]
            return None
        else:
            return None
    except FileNotFoundError:
        return None
    finally:
        winreg.CloseKey(reg_key)


def get_system_proxy_unix():
    http_proxy = os.getenv("http_proxy")
    https_proxy = os.getenv("https_proxy")

    if http_proxy or https_proxy:

        if http_proxy and ':' in http_proxy:
            return http_proxy.split(":")[-1]
        elif https_proxy and ':' in https_proxy:
            return https_proxy.split(":")[-1]
    return None


def can_access_google():
    try:
        response = requests.get("http://www.google.com", timeout=5)
        if response.status_code == 200:
            return True
    except requests.RequestException:
        return False
    return False


def set_proxy_env(port):
    if port == "-1":
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)

    else:
        os.environ['http_proxy'] = f'http://127.0.0.1:{port}'
        os.environ['https_proxy'] = f'http://127.0.0.1:{port}'


def clear_proxy_env():
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)


def auto_detect_proxy():
    clear_proxy_env()
    user_input_port = proxy_port_entry.get()
    if user_input_port:
        if check_proxy(user_input_port):
            set_proxy_env(user_input_port)
            return
        else:
            messagebox.showwarning(
                "警告", f"输入的代理端口 {user_input_port} 无效，正在尝试自动检测代理。")
    if can_access_google():
        set_proxy_env("-1")
        proxy_port_entry.delete(0, tk.END)
        proxy_port_entry.insert(0, "-1")
        messagebox.showinfo("信息", "已检测到本地可以直接访问Google，代理已禁用。")
        return

    default_ports = [7890, 1080, 8080]
    for port in default_ports:
        if check_proxy(port):
            set_proxy_env(port)
            proxy_port_entry.delete(0, tk.END)
            proxy_port_entry.insert(0, port)
            return

    messagebox.showwarning("警告", "未找到可用的代理端口")


def check_proxy(port):
    proxy_address = ("127.0.0.1", int(port))
    try:
        with socket.create_connection(proxy_address, timeout=5) as sock:
            connect_request = b"CONNECT www.google.com:443 HTTP/1.1\r\nHost: www.google.com:443\r\n\r\n"
            sock.sendall(connect_request)
            response = sock.recv(4096)
            if b"200 Connection established" in response:
                return True
    except socket.error:
        return False
    return False


def start_python_script(Alert=True):
    if check_singleton_title("Copilot_Whisper_Mic"):
        if Alert:
            messagebox.showinfo("信息", "Copilot_Whisper_Mic 已经在运行")
        return
    openai_key = openai_key_entry.get()
    proxy_port = proxy_port_entry.get()

    if not openai_key:
        messagebox.showerror("错误", "请设置OPENAI_API_KEY")
        return False

    if not proxy_port:
        messagebox.showerror("错误", "请设置代理端口或禁用代理")
        return False

    os.environ['OPENAI_API_KEY'] = openai_key
    set_proxy_env(proxy_port)
    mic_mode = selected_mic_version.get()
    command = [os.path.join("openra_ai", "start.bat")]

    if mic_mode == "手动输入":
        command.append("--input_mode")
        command.append("keyboard")

    subprocess.Popen(command, env=os.environ, creationflags=subprocess.CREATE_NEW_CONSOLE)

    return True


def start_openra(Alert=True):
    if not check_singleton("RedAlert.exe"):
        openra_path = "build/RedAlert.exe"
        subprocess.Popen([openra_path])
    elif Alert:
        messagebox.showinfo("信息", "OpenRA 已经在运行")


def one_click_start():
    setup_environment(False)
    if not proxy_port_entry.get():
        auto_detect_proxy()
    if start_python_script(False):
        start_openra(False)


def check_singleton(process_name):
    for proc in psutil.process_iter():
        try:
            if process_name.lower() in proc.name().lower():
                return True
        except psutil.NoSuchProcess:
            pass
    return False


def check_singleton_title(title):
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        return False
    return True


def terminate_process_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            try:
                proc.terminate()
                proc.wait()
                return True
            except psutil.NoSuchProcess:
                return False
    return False


def terminate_process_by_window_title(title):
    windows = gw.getWindowsWithTitle(title)

    if not windows:
        return False

    for window in windows:
        hwnd = window._hWnd
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(
            hwnd, ctypes.byref(pid))
        pid_value = pid.value

        try:

            for proc in psutil.process_iter(['pid', 'name']):
                if proc.pid == pid_value:
                    print(f"正在终止进程: {proc.info['name']} (PID: {proc.pid})")
                    proc.terminate()
                    proc.wait()
                    return True
        except psutil.NoSuchProcess:
            print(f"进程已不存在")
            return False

    return False


def get_latest_release(startup=False):
    try:
        url = "https://api.github.com/repos/OpenRA-CopilotTestGroup/OpenRA/releases"
        response = requests.get(url)
        releases = response.json()

        for release in releases:
            return release['tag_name'].lstrip('v'), release['assets'][0]['browser_download_url']
    except Exception as e:
        if not startup:
            messagebox.showerror("错误", f"检查更新时出现错误：{e}")


def check_for_updates(startup=False):
    global update_available, latest_version, download_url
    try:
        latest_version, download_url = get_latest_release()

        if latest_version > VERSION:
            update_available = True
            if startup:

                auto_update_button.config(text="有新版本！", bg="red", fg="white")
            else:
                prompt_update(latest_version, download_url)
        else:
            update_available = False
            if not startup:
                messagebox.showinfo("提示", "当前已是最新版本")

    except Exception as e:
        if not startup:
            messagebox.showerror("错误", f"检查更新时出现错误：{e}")


def prompt_update(latest_version, download_url):
    result = messagebox.askyesno("更新可用", f"检测到新版本 {latest_version}，是否下载并安装？")
    if result:
        download_and_replace(download_url)


def download_and_replace(download_url):
    def download_task(progress, root, label, speed_label):
        try:
            proxy_port = proxy_port_entry.get()
            proxies = {"http": f'http://127.0.0.1:{proxy_port}',
                       "https": f'http://127.0.0.1:{proxy_port}'} if proxy_port else None

            response = requests.get(download_url, stream=True, proxies=proxies)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 65536
            zip_file = "launcher_update.zip"

            downloaded_size = 0
            start_time = time.time()
            if response.status_code == 200:
                with open(zip_file, "wb") as f:
                    for chunk in response.iter_content(block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            root.update_idletasks()

                            percent = (downloaded_size / total_size) * 100
                            progress["value"] = percent
                            label.config(text=f"正在下载更新... {percent:.2f}%")

                            elapsed_time = time.time() - start_time
                            speed = downloaded_size / elapsed_time

                            if speed > 1024 * 1024:
                                speed_label.config(
                                    text=f"下载速度：{speed / (1024 * 1024):.2f} MB/s")
                            else:
                                speed_label.config(
                                    text=f"下载速度：{speed / 1024:.2f} KB/s")

                root.destroy()
                root.after(0, replace_and_restart_thread, zip_file, root)
            else:
                root.destroy()
                messagebox.showerror("错误", "下载更新失败")
        except Exception as e:
            root.after(0, root.destroy)
            messagebox.showerror("错误", f"下载更新时出现错误：{e}")

    def replace_and_restart_thread(zip_file, root):
        replace_and_restart(zip_file)
        root.after(0, root.destroy)

    def start_download():

        download_window = Tk()
        download_window.title("下载进度")
        download_window.geometry("300x150")

        progress = ttk.Progressbar(
            download_window, orient="horizontal", length=200, mode="determinate")
        progress.pack(pady=10)
        progress["maximum"] = 100

        label = ttk.Label(download_window, text="正在下载更新... 0%")
        label.pack()

        speed_label = ttk.Label(download_window, text="下载速度：0 KB/s")
        speed_label.pack()

        download_window.grab_set()

        download_thread = threading.Thread(target=download_task, args=(
            progress, download_window, label, speed_label))
        download_thread.start()

        download_window.mainloop()

    start_download()


def replace_and_restart(zip_file):
    result = messagebox.askokcancel("升级确认", "下载完成，确认升级将重启当前进程")

    if result:
        print("继续执行后续操作")

    else:
        return
    terminate_process_by_name("RedAlert.exe")
    terminate_process_by_window_title("Copilot_Whisper_Mic")

    current_process_name = psutil.Process(os.getpid()).name()

    temp_dir = "temp_update"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    new_exe_file = os.path.join(temp_dir, "Starter.exe")

    if os.path.exists(new_exe_file):
        print(f"找到新的启动器: {new_exe_file}")
        shutil.move(new_exe_file, "Starter_new.exe")
        run_update_bat(current_process_name, temp_dir)

    else:
        print("未找到 Starter.exe 文件")


def run_update_bat(current_process_name, temp_dir):
    bat_content = f"""
        @echo off
        echo 升级中...请勿关闭此窗口
        timeout /t 3 /nobreak > NUL
        mkdir backup
        rmdir /s /q "backup\\build" >nul 2>nul
        rmdir /s /q "backup\\openra_ai" >nul 2>nul
        move build backup
        move openra_ai backup
        move /y "{current_process_name}" "backup\\Starter_old.exe"
        move /y "Starter_new.exe" "{current_process_name}"
        rmdir /s /q "build" >nul 2>nul
        rmdir /s /q "openra_ai" >nul 2>nul
        move {temp_dir}\\build build
        move {temp_dir}\\openra_ai openra_ai
        rmdir /s /q "{temp_dir}"
        start "" "{current_process_name}"
        start "" cmd /c del "%~f0"
        """
    with open("update.bat", "w") as f:
        f.write(bat_content)

    subprocess.Popen("update.bat", creationflags=subprocess.CREATE_NEW_CONSOLE)

    root.destroy()


def update_button():
    if not update_available:
        check_for_updates()
    if update_available:
        prompt_update(latest_version, download_url)


if not hasattr(sys, '_MEIPASS'):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录已更改为: {os.getcwd()}")

current_exe = sys.argv[0]
print(current_exe)
if "_new" in current_exe:
    new_exe_name = current_exe.replace("_new", "")
    time.sleep(1)
    shutil.copy(current_exe, new_exe_name)
    subprocess.Popen(new_exe_name)
    sys.exit()
update_available = False
check_for_updates(startup=True)

terminate_process_by_window_title("OpenRA - Red Alert")
root = tk.Tk()
root.title("Copilot-OpenRA启动器" + " v" + VERSION)

root.geometry("350x300")
root.configure(bg="#f0f0f0")

root.grid_columnconfigure(0, weight=1, uniform="col")
root.grid_columnconfigure(1, weight=8, uniform="col")
root.grid_columnconfigure(2, weight=8, uniform="col")
root.grid_columnconfigure(3, weight=1, uniform="col")
root.grid_rowconfigure(0, weight=1, uniform="row")
root.grid_rowconfigure(1, weight=2, uniform="row")
root.grid_rowconfigure(2, weight=2, uniform="row")
root.grid_rowconfigure(3, weight=3, uniform="row")
root.grid_rowconfigure(4, weight=3, uniform="row")
root.grid_rowconfigure(5, weight=6, uniform="row")
root.grid_rowconfigure(6, weight=1, uniform="row")

openai_key_label = tk.Label(root, text="OPENAI-KEY:", bg="#f0f0f0")
openai_key_label.grid(row=1, column=0, columnspan=2,
                      padx=(20, 0), pady=5, sticky="w")

openai_key_entry = tk.Entry(root)
openai_key_entry.grid(row=1, column=0, columnspan=3,
                      padx=(120, 10), pady=5, sticky="we")

proxy_port_label = tk.Label(root, text="设置代理端口:", bg="#f0f0f0")
proxy_port_label.grid(row=2, column=0, columnspan=2,
                      padx=(20, 0), pady=5, sticky="w")

proxy_port_entry = tk.Entry(root, width=6)
proxy_port_entry.grid(row=2, column=0, columnspan=2,
                      padx=(120, 10), pady=5, sticky="w")

button_font = ("Microsoft YaHei", 10)

gpt_versions = ["GPT-3.5", "GPT-4", "GPT-4o",
                "GPT-4o mini", "GPT-o1", "目前仅测试用，无实际效果"]

selected_version = StringVar(root)
selected_version.set("GPT-4o")

dropdown = tk.OptionMenu(root, selected_version, *gpt_versions)
dropdown.grid(row=3, column=1, padx=(15, 15), pady=5, sticky="we")

selected_mic_version = StringVar(root)
selected_mic_version.set("openai")

mic_versions = ["openai", "手动输入"]

dropdown_mic = tk.OptionMenu(root, selected_mic_version, *mic_versions)
dropdown_mic.grid(row=3, column=2, padx=(15, 15), pady=5, sticky="we")


# install_button = tk.Button(root, text="安装Python",
#                            command=install_python, font=button_font)
# install_button.grid(row=3, column=1, padx=(15, 15), pady=5, sticky="we")

start_python_button = tk.Button(
    root, text="启动语音识别", command=start_python_script, font=button_font)
start_python_button.grid(row=4, column=2, padx=(15, 15), pady=5, sticky="we")

start_openra_button = tk.Button(
    root, text="启动OpenRA", command=start_openra, font=button_font)
start_openra_button.grid(row=4, column=1, padx=(15, 15), pady=5, sticky="we")

auto_proxy_button = tk.Button(
    root, text="自动设置代理端口", command=auto_detect_proxy, font=button_font)
auto_proxy_button.grid(row=2, column=2, padx=(15, 15), pady=5, sticky="we")

one_click_button = tk.Button(
    root, text="一键启动！", command=one_click_start, font=("Microsoft YaHei", 18))
one_click_button.grid(row=5, column=1, columnspan=2,
                      pady=10, ipadx=50, ipady=10)

if update_available:
    auto_update_button = tk.Button(
        root, text="U！", command=update_button, font=button_font, width=3, bg="red", fg="white")
else:
    auto_update_button = tk.Button(
        root, text="U", command=update_button, font=button_font, width=3)

auto_update_button.grid(row=5, rowspan=2, column=2, columnspan=2, padx=(
    10, 10), pady=(10, 10), sticky="es")

# debug_button = tk.Button(root, text="D",  command=lambda: replace_and_restart(
#     "launcher_update.zip"), font=button_font, width=3)
# debug_button.grid(row=5, rowspan=2, column=0, columnspan=2,
#                   padx=(10, 10), pady=(10, 10), sticky="es")

load_settings()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
