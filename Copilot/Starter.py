import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import psutil
import requests
import socket
import configparser

CONFIG_FILE = "settings.ini"

def load_settings():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        if "Settings" in config:
            openai_key_entry.insert(0, config.get("Settings", "OPENAI_KEY", fallback=""))
            proxy_port_entry.insert(0, config.get("Settings", "PROXY_PORT", fallback=""))

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

def setup_environment(alter = True):
    if not check_python_installed():
        install_python()
    elif alter:
        messagebox.showinfo("信息", "Python 环境已安装")

def install_python():
    python_installer = "static\\python-3.12.6-amd64.exe"  
    if os.path.exists(python_installer):
        subprocess.run([python_installer], check=True)
        
        subprocess.run(["python", "-m", "pip", "install", "-e", "."], check=True)
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
            messagebox.showwarning("警告", f"输入的代理端口 {user_input_port} 无效，正在尝试自动检测代理。")
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

def start_python_script():
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
    subprocess.Popen([os.path.join("openra_ai", "start.bat")], env=os.environ, creationflags=subprocess.CREATE_NEW_CONSOLE)
    return True

def start_openra():
    if not check_singleton("RedAlert.exe"):
        openra_path = "build/RedAlert.exe"
        subprocess.Popen([openra_path])
    else:
        messagebox.showinfo("信息", "OpenRA 已经在运行")

def one_click_start():
    setup_environment(False)
    if not proxy_port_entry.get():
        auto_detect_proxy()
    if start_python_script():
        start_openra()

def check_singleton(process_name):
    for proc in psutil.process_iter():
        try:
            if process_name.lower() in proc.name().lower():
                return True
        except psutil.NoSuchProcess:
            pass
    return False

def auto_update():
    return

root = tk.Tk()
root.title("Copilot-OpenRA启动器")

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
openai_key_label.grid(row=1, column=0,columnspan=2, padx=(20,0), pady=5, sticky="w")

openai_key_entry = tk.Entry(root)
openai_key_entry.grid(row=1, column=0,columnspan=3, padx=(120,10), pady=5, sticky="we")

proxy_port_label = tk.Label(root, text="设置代理端口:", bg="#f0f0f0")
proxy_port_label.grid(row=2, column=0,columnspan=2, padx=(20,0), pady=5, sticky="w")

proxy_port_entry = tk.Entry(root, width=6)
proxy_port_entry.grid(row=2, column=0,columnspan=2, padx=(120,10), pady=5, sticky="w")

button_font = ("Microsoft YaHei", 10)

install_button = tk.Button(root, text="安装Python", command=install_python, font=button_font)
install_button.grid(row=3, column=1, padx=(15,15), pady=5, sticky="we")

start_python_button = tk.Button(root, text="启动语音识别", command=start_python_script, font=button_font)
start_python_button.grid(row=3, column=2, padx=(15,15), pady=5, sticky="we")

start_openra_button = tk.Button(root, text="启动OpenRA", command=start_openra, font=button_font)
start_openra_button.grid(row=4, column=1, padx=(15,15), pady=5, sticky="we")

auto_proxy_button = tk.Button(root, text="自动设置代理端口", command=auto_detect_proxy, font=button_font)
auto_proxy_button.grid(row=4, column=2, padx=(15,15), pady=5, sticky="we")

one_click_button = tk.Button(root, text="一键启动！", command=one_click_start, font=("Microsoft YaHei", 18))
one_click_button.grid(row=5, column=1, columnspan=2, pady=10, ipadx=50, ipady=10)

auto_update_button = tk.Button(root, text="U", command=auto_update, font=button_font, width=2,height=1)
auto_update_button.grid(row=5, rowspan=2, column=2, columnspan=2, padx=(10,10), pady=(10,10), sticky="es")

load_settings()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
