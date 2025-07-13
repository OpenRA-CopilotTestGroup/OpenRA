import asyncio
import cv2
import numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription
from aiortc.contrib.signaling import BYE
from av import VideoFrame
import argparse
import subprocess
import sys
import traceback
import os
import time
import tempfile
import threading
from collections import deque
import json
import socket

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=8080)
args = parser.parse_args()
port = args.port

# 游戏状态管理
game_process = None
game_socket = None
game_socket_lock = asyncio.Lock()

import uuid

def generate_request_id():
    """生成请求ID"""
    return str(uuid.uuid4())

def format_command_json(command_data):
    """格式化命令JSON，补齐默认字段"""
    if isinstance(command_data, str):
        try:
            command_data = json.loads(command_data)
        except json.JSONDecodeError:
            raise ValueError("无效的JSON格式")
    
    # 补齐默认字段
    formatted = {
        "apiVersion": "1.0",
        "requestId": generate_request_id(),
        "language": "zh"
    }
    
    # 如果输入的是完整格式，保留原有字段
    if "apiVersion" in command_data:
        formatted["apiVersion"] = command_data["apiVersion"]
    if "requestId" in command_data:
        formatted["requestId"] = command_data["requestId"]
    if "language" in command_data:
        formatted["language"] = command_data["language"]
    
    # 处理命令字段
    if "command" in command_data:
        formatted["command"] = command_data["command"]
        # 如果有params，保留params
        if "params" in command_data:
            formatted["params"] = command_data["params"]
        # 如果没有params，但有其他字段，将它们作为params
        else:
            params = {}
            for key, value in command_data.items():
                if key not in ["apiVersion", "requestId", "language", "command"]:
                    params[key] = value
            if params:
                formatted["params"] = params
    else:
        # 如果没有command字段，将整个对象作为params，command设为"custom"
        formatted["command"] = "custom"
        formatted["params"] = command_data
    
    return formatted

async def connect_to_game_socket():
    """连接到游戏socket"""
    global game_socket
    async with game_socket_lock:
        if game_socket is None:
            try:
                game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                game_socket.connect(('localhost', 7445))
                print("✅ 已连接到游戏socket (端口7445)")
                return True
            except Exception as e:
                print(f"❌ 连接游戏socket失败: {e}")
                game_socket = None
                return False
        return True

async def send_to_game_socket(data):
    """发送数据到游戏socket"""
    global game_socket
    
    # 格式化命令JSON
    try:
        formatted_data = format_command_json(data)
        data_str = json.dumps(formatted_data, ensure_ascii=False)
    except Exception as e:
        raise ValueError(f"JSON格式化失败: {e}")
    
    # 尝试连接
    if not await connect_to_game_socket():
        raise ConnectionError("无法连接到游戏socket")
    
    try:
        # 发送UTF-8编码的数据
        message = data_str.encode('utf-8') + b'\n'
        game_socket.send(message)
        print(f"✅ 已发送数据到游戏: {data_str}")
        return True
    except Exception as e:
        print(f"❌ 发送数据失败: {e}")
        # 重置连接
        if game_socket:
            try:
                game_socket.close()
            except:
                pass
            game_socket = None
        raise ConnectionError(f"发送数据失败: {e}")

def start_game(load_save="01"):
    """启动游戏"""
    global game_process
    try:
        # 先检查是否已有游戏在运行
        if is_game_running():
            print("游戏已经在运行中")
            return False
        
        # 确保没有残留进程
        force_kill_game_process()
        
        # 切换到OpenRA根目录
        openra_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        launch_script = os.path.join(openra_dir, "launch-game.sh")
        
        if not os.path.exists(launch_script):
            raise FileNotFoundError(f"启动脚本不存在: {launch_script}")
        
        print(f"正在启动游戏，LoadSave: {load_save}")
        
        # 启动游戏
        cmd = [launch_script, f"Game.Mod=copilot", f"Game.LoadSave={load_save}"]
        game_process = subprocess.Popen(cmd, cwd=openra_dir)
        
        # 等待一下让进程启动
        time.sleep(2)
        
        # 验证进程是否真的启动了
        if game_process.poll() is not None:
            # 进程立即退出了
            print(f"❌ 游戏进程启动失败，退出码: {game_process.returncode}")
            game_process = None
            return False
        
        # 通过系统命令再次确认
        try:
            result = subprocess.run(["pgrep", "-f", "Game.Mod=copilot"], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                print(f"✅ 游戏启动成功，PID: {game_process.pid}, LoadSave: {load_save}")
                return True
            else:
                print("❌ 游戏进程启动失败，系统未检测到进程")
                game_process = None
                return False
        except Exception as e:
            print(f"⚠️ 进程验证失败: {e}")
            # 如果验证失败，但进程对象还在，认为启动成功
            if game_process.poll() is None:
                print(f"✅ 游戏启动成功，PID: {game_process.pid}, LoadSave: {load_save}")
                return True
            else:
                game_process = None
                return False
        
    except Exception as e:
        print(f"❌ 启动游戏失败: {e}")
        game_process = None
        return False

def stop_game():
    """停止游戏"""
    global game_process, game_socket
    try:
        if game_process:
            # 检查进程是否还在运行
            if game_process.poll() is None:
                print("正在尝试正常停止游戏...")
                game_process.terminate()
                
                # 等待进程结束，最多等待10秒
                try:
                    game_process.wait(timeout=10)
                    print("✅ 游戏已正常停止")
                except subprocess.TimeoutExpired:
                    print("⚠️ 游戏未响应，正在强制停止...")
                    game_process.kill()
                    try:
                        game_process.wait(timeout=5)
                        print("✅ 游戏已强制停止")
                    except subprocess.TimeoutExpired:
                        print("⚠️ 强制停止超时，尝试使用系统命令...")
                        # 使用系统命令强制杀死进程
                        force_kill_game_process()
            else:
                print("游戏进程已经结束")
        else:
            print("游戏未运行")
        
        # 关闭socket连接
        if game_socket:
            try:
                game_socket.close()
            except:
                pass
            game_socket = None
            print("✅ 游戏socket连接已关闭")
        
        game_process = None
        return True
        
    except Exception as e:
        print(f"❌ 停止游戏失败: {e}")
        # 即使出错也要尝试强制清理
        force_kill_game_process()
        game_process = None
        return True

def force_kill_game_process():
    """强制杀死游戏相关进程"""
    try:
        # 查找并杀死OpenRA相关进程
        kill_commands = [
            ["pkill", "-f", "OpenRA"],
            ["pkill", "-f", "launch-game.sh"],
            ["pkill", "-f", "Game.Mod=copilot"],
        ]
        
        for cmd in kill_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ 已强制停止进程: {' '.join(cmd)}")
            except Exception as e:
                print(f"⚠️ 强制停止命令失败: {' '.join(cmd)} - {e}")
        
        # 等待一下让进程完全结束
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ 强制清理失败: {e}")

def is_game_running():
    """检查游戏是否在运行"""
    global game_process
    
    # 检查进程对象
    if game_process is None:
        return False
    
    # 检查进程是否还在运行
    if game_process.poll() is not None:
        # 进程已经结束，清理引用
        game_process = None
        return False
    
    # 额外检查：通过系统命令确认进程是否真的在运行
    try:
        # 检查OpenRA相关进程
        result = subprocess.run(["pgrep", "-f", "Game.Mod=copilot"], 
                              capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return True
        else:
            # 系统命令显示进程不存在，但我们的引用还在，需要清理
            print("⚠️ 检测到进程引用不一致，正在清理...")
            game_process = None
            return False
    except Exception as e:
        print(f"⚠️ 进程检查异常: {e}")
        # 如果检查失败，相信我们的进程引用
        return game_process.poll() is None

# 捕获方法列表
CAPTURE_METHODS = [
    {"name": "屏幕截图", "desc": "Screen capture (screencapture)", "arg": "screencapture"},
    {"name": "测试帧", "desc": "彩色测试帧", "arg": None},
]
capture_method_index = 0  # 默认使用第一个方法

# 分辨率选项
RESOLUTION_OPTIONS = [
    {"name": "480p", "width": 854, "height": 480},
    {"name": "720p", "width": 1280, "height": 720},
    {"name": "1080p", "width": 1920, "height": 1080},
    {"name": "1440p", "width": 2560, "height": 1440},
    {"name": "4K", "width": 3840, "height": 2160},
]
resolution_index = 1  # 默认使用720p

class SmartScreenCapture:
    """智能屏幕捕获类"""
    def __init__(self, max_fps=30, min_fps=5, target_width=1280, target_height=720):
        self.max_fps = max_fps
        self.min_fps = min_fps
        self.current_fps = 15
        self.last_frame = None
        self.last_capture_time = 0
        self.frame_history = deque(maxlen=10)  # 保存最近10帧用于变化检测
        self.network_quality = 1.0  # 网络质量指标 (0.0-1.0)
        self.motion_threshold = 0.02  # 运动检测阈值
        self.temp_file = None
        self.target_width = target_width
        self.target_height = target_height
        self.setup_temp_file()
        
    def setup_temp_file(self):
        """设置临时文件"""
        try:
            self.temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.temp_file.close()
            print(f"✅ 智能截图临时文件创建成功: {self.temp_file.name}")
        except Exception as e:
            print(f"❌ 智能截图临时文件创建失败: {e}")
            self.temp_file = None
    
    def update_resolution(self, width, height):
        """更新目标分辨率"""
        self.target_width = width
        self.target_height = height
        print(f"✅ 分辨率已更新为: {width}x{height}")
    
    def calculate_frame_difference(self, frame1, frame2):
        """计算两帧之间的差异"""
        if frame1 is None or frame2 is None:
            return 1.0
        
        # 转换为灰度图
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # 计算差异
        diff = cv2.absdiff(gray1, gray2)
        mean_diff = np.mean(diff) / 255.0
        
        return mean_diff
    
    def detect_motion(self, current_frame):
        """检测运动"""
        if len(self.frame_history) < 2:
            return True
        
        # 计算与上一帧的差异
        last_frame = self.frame_history[-1]
        motion_level = self.calculate_frame_difference(last_frame, current_frame)
        
        return motion_level > self.motion_threshold
    
    def adjust_fps_based_on_motion(self, has_motion):
        """根据运动情况调整帧率"""
        if has_motion:
            # 有运动时，根据网络质量调整帧率
            target_fps = int(self.max_fps * self.network_quality)
            self.current_fps = max(self.min_fps, min(self.max_fps, target_fps))
        else:
            # 无运动时，降低帧率
            self.current_fps = max(self.min_fps, self.current_fps // 2)
    
    def update_network_quality(self, quality):
        """更新网络质量指标"""
        self.network_quality = max(0.1, min(1.0, quality))
        print(f"网络质量更新: {self.network_quality:.2f}")
    
    def capture_frame(self):
        """捕获一帧"""
        if not self.temp_file:
            return None
        
        current_time = time.time()
        frame_interval = 1.0 / self.current_fps
        
        # 检查是否需要捕获新帧
        if current_time - self.last_capture_time < frame_interval:
            # 返回上一帧
            return self.last_frame
        
        try:
            # 截图
            cmd = ['screencapture', '-x', self.temp_file.name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0 and os.path.exists(self.temp_file.name):
                frame = cv2.imread(self.temp_file.name)
                if frame is not None:
                    # 检测运动
                    has_motion = self.detect_motion(frame)
                    
                    # 调整帧率
                    self.adjust_fps_based_on_motion(has_motion)
                    
                    # 更新历史
                    self.frame_history.append(frame.copy())
                    self.last_frame = frame
                    self.last_capture_time = current_time
                    
                    if has_motion:
                        print(f"检测到运动，帧率: {self.current_fps}fps")
                    
                    return frame
        except Exception as e:
            print(f"智能截图异常: {e}")
        
        return self.last_frame

class ScreenTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        global capture_method_index, resolution_index
        method = CAPTURE_METHODS[capture_method_index]
        resolution = RESOLUTION_OPTIONS[resolution_index]
        print(f"当前捕获方法: {method['name']} - {method['desc']}")
        print(f"当前分辨率: {resolution['name']} ({resolution['width']}x{resolution['height']})")
        
        if method["arg"] is None:
            # 使用测试帧
            self.cap = None
            self.temp_file = None
            self.smart_capture = None
            self.target_width = resolution['width']
            self.target_height = resolution['height']
            print("使用测试帧模式")
        elif method["arg"] == "screencapture":
            # 使用 screencapture 方法
            self.cap = None
            self.temp_file = None
            self.smart_capture = None
            self.target_width = resolution['width']
            self.target_height = resolution['height']
            self.setup_screencapture()
        elif method["arg"] == "smart_screencapture":
            # 使用智能 screencapture 方法
            self.cap = None
            self.temp_file = None
            self.smart_capture = SmartScreenCapture(
                target_width=resolution['width'], 
                target_height=resolution['height']
            )
            print("✅ 智能屏幕捕获初始化成功")
        elif isinstance(method["arg"], int):
            # 摄像头
            self.cap = cv2.VideoCapture(method["arg"])
            self.temp_file = None
            self.smart_capture = None
            self.target_width = resolution['width']
            self.target_height = resolution['height']
            if self.cap and self.cap.isOpened():
                print(f"✅ 摄像头 {method['arg']} 打开成功")
            else:
                print(f"❌ 摄像头 {method['arg']} 打开失败，使用测试帧")
                self.cap = None
    
    def update_resolution(self, width, height):
        """更新分辨率"""
        self.target_width = width
        self.target_height = height
        if self.smart_capture:
            self.smart_capture.update_resolution(width, height)
        print(f"✅ 视频轨道分辨率已更新为: {width}x{height}")
    
    def setup_screencapture(self):
        """设置基于 screencapture 的屏幕捕获"""
        try:
            self.temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.temp_file.close()
            print(f"✅ screencapture 临时文件创建成功: {self.temp_file.name}")
        except Exception as e:
            print(f"❌ screencapture 临时文件创建失败: {e}")
            self.temp_file = None

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 保持宽高比的resize
                frame = self.resize_with_aspect_ratio(frame, max_width=self.target_width, max_height=self.target_height)
            else:
                # 如果读取失败，创建测试帧
                frame = self.create_test_frame()
        elif self.smart_capture:
            # 使用智能屏幕捕获
            frame = self.smart_capture.capture_frame()
            if frame is not None:
                # 保持宽高比的resize
                frame = self.resize_with_aspect_ratio(frame, max_width=self.target_width, max_height=self.target_height)
            else:
                frame = self.create_test_frame()
        elif self.temp_file and self.temp_file.name.endswith('.png'):
            # 使用 screencapture
            try:
                current_time = time.time()
                if not hasattr(self, 'last_capture_time') or current_time - self.last_capture_time > 0.0416:  # 每秒截图24次
                    self.last_capture_time = current_time
                    
                    # 截图
                    cmd = ['screencapture', '-x', self.temp_file.name]
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode != 0:
                            print(f"截图失败: {result.stderr}")
                    except Exception as e:
                        print(f"截图异常: {e}")
                
                # 读取截图
                if os.path.exists(self.temp_file.name):
                    frame = cv2.imread(self.temp_file.name)
                    if frame is not None:
                        # 保持宽高比的resize
                        frame = self.resize_with_aspect_ratio(frame, max_width=self.target_width, max_height=self.target_height)
                    else:
                        frame = self.create_test_frame()
                else:
                    frame = self.create_test_frame()
                    
            except Exception as e:
                print(f"screencapture 读取失败: {e}")
                frame = self.create_test_frame()
        else:
            # 如果没有摄像头，创建测试帧
            frame = self.create_test_frame()
        
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = pts
        new_frame.time_base = time_base
        return new_frame
    
    def resize_with_aspect_ratio(self, frame, max_width=1280, max_height=720):
        """保持宽高比的resize"""
        height, width = frame.shape[:2]
        
        # 计算缩放比例
        scale_width = max_width / width
        scale_height = max_height / height
        scale = min(scale_width, scale_height)  # 使用较小的缩放比例以保持宽高比
        
        # 计算新的尺寸
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # 如果尺寸没有变化，直接返回
        if new_width == width and new_height == height:
            return frame
        
        # 执行resize
        resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # 如果需要，创建固定尺寸的画布并居中放置
        if new_width < max_width or new_height < max_height:
            canvas = np.zeros((max_height, max_width, 3), dtype=np.uint8)
            
            # 计算居中位置
            x_offset = (max_width - new_width) // 2
            y_offset = (max_height - new_height) // 2
            
            # 将resized图像放置到画布中心
            canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized_frame
            return canvas
        
        return resized_frame
    
    def create_test_frame(self):
        """创建测试帧"""
        # 创建一个彩色的测试帧
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # 添加一些彩色条纹
        colors = [
            (255, 0, 0),    # 红色
            (0, 255, 0),    # 绿色
            (0, 0, 255),    # 蓝色
            (255, 255, 0),  # 黄色
            (255, 0, 255),  # 洋红
            (0, 255, 255),  # 青色
        ]
        
        stripe_height = 720 // len(colors)
        for i, color in enumerate(colors):
            y1 = i * stripe_height
            y2 = (i + 1) * stripe_height
            frame[y1:y2, :] = color
        
        # 添加文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, 'OpenRA Copilot Test Frame', (50, 360), font, 2, (255, 255, 255), 3)
        cv2.putText(frame, 'No camera detected', (50, 420), font, 1, (255, 255, 255), 2)
        
        return frame
    
    def stop(self):
        """停止视频捕获"""
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
                print(f"临时文件 {self.temp_file.name} 已删除")
            except Exception as e:
                print(f"删除临时文件失败: {e}")
            self.temp_file = None

pcs = set()

async def offer(request):
    try:
        params = await request.json()
        
        # 验证参数
        if "sdp" not in params or "type" not in params:
            return web.json_response({"error": "Missing sdp or type parameter"}, status=400)
        
        pc = RTCPeerConnection()
        pcs.add(pc)

        # 创建视频轨道
        video_track = ScreenTrack()
        pc.addTrack(video_track)

        # 创建 RTCSessionDescription 对象
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # 设置网络质量监控
        async def monitor_network_quality():
            while pc.connectionState != 'closed':
                try:
                    # 获取连接统计信息
                    stats = await pc.getStats()
                    
                    # 分析网络质量
                    network_quality = analyze_network_quality(stats)
                    
                    # 更新智能捕获的网络质量
                    if hasattr(video_track, 'smart_capture') and video_track.smart_capture:
                        video_track.smart_capture.update_network_quality(network_quality)
                    
                    await asyncio.sleep(5)  # 每5秒检查一次
                except Exception as e:
                    print(f"网络质量监控异常: {e}")
                    break
        
        # 启动网络质量监控
        asyncio.create_task(monitor_network_quality())

        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    
    except Exception as e:
        print(f"Error in offer handler: {e}")
        print(traceback.format_exc())
        return web.json_response({"error": str(e)}, status=500)

def analyze_network_quality(stats):
    """分析网络质量"""
    try:
        # 这里可以添加更复杂的网络质量分析逻辑
        # 目前返回一个简单的质量指标
        return 0.8  # 默认质量80%
    except Exception as e:
        print(f"网络质量分析异常: {e}")
        return 0.5  # 默认质量50%

async def index(request):
    response = web.FileResponse("index.html")
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

async def set_capture_mode(request):
    global capture_method_index
    try:
        data = await request.json()
        index_change = data.get('index')
        if index_change is not None:
            new_index = int(index_change)
            if 0 <= new_index < len(CAPTURE_METHODS):
                capture_method_index = new_index
                print(f"捕获方法已切换为: {CAPTURE_METHODS[capture_method_index]['name']}")
                return web.json_response({'status': 'ok', 'index': capture_method_index})
            else:
                return web.json_response({'error': 'Invalid index'}, status=400)
        else:
            return web.json_response({'error': 'Missing index parameter'}, status=400)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def set_resolution(request):
    global resolution_index
    try:
        data = await request.json()
        index_change = data.get('index')
        if index_change is not None:
            new_index = int(index_change)
            if 0 <= new_index < len(RESOLUTION_OPTIONS):
                resolution_index = new_index
                resolution = RESOLUTION_OPTIONS[resolution_index]
                print(f"分辨率已切换为: {resolution['name']} ({resolution['width']}x{resolution['height']})")
                return web.json_response({
                    'status': 'ok', 
                    'index': resolution_index,
                    'resolution': resolution
                })
            else:
                return web.json_response({'error': 'Invalid resolution index'}, status=400)
        else:
            return web.json_response({'error': 'Missing index parameter'}, status=400)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def get_capture_methods(request):
    """获取所有可用的捕获方法"""
    try:
        methods = [{"index": i, "name": method["name"]} for i, method in enumerate(CAPTURE_METHODS)]
        return web.json_response({"methods": methods, "current_index": capture_method_index})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def get_resolutions(request):
    """获取所有可用的分辨率选项"""
    try:
        resolutions = [{"index": i, "name": res["name"], "width": res["width"], "height": res["height"]} 
                      for i, res in enumerate(RESOLUTION_OPTIONS)]
        return web.json_response({"resolutions": resolutions, "current_index": resolution_index})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def start_game_endpoint(request):
    """启动游戏API"""
    try:
        data = await request.json()
        load_save = data.get('load_save', '01')
        
        if start_game(load_save):
            return web.json_response({'status': 'ok', 'message': f'游戏启动成功，LoadSave: {load_save}'})
        else:
            return web.json_response({'error': '游戏启动失败'}, status=500)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def stop_game_endpoint(request):
    """停止游戏API"""
    try:
        if stop_game():
            return web.json_response({'status': 'ok', 'message': '游戏已停止'})
        else:
            return web.json_response({'error': '游戏停止失败'}, status=500)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def game_status(request):
    """获取游戏状态"""
    try:
        running = is_game_running()
        return web.json_response({'running': running})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def send_command(request):
    """发送命令到游戏"""
    try:
        data = await request.json()
        command = data.get('command', '')
        
        if not command:
            return web.json_response({'error': '命令不能为空'}, status=400)
        
        # 检查游戏是否运行
        if not is_game_running():
            return web.json_response({'error': '游戏未运行'}, status=400)
        
        await send_to_game_socket(command)
        return web.json_response({'status': 'ok', 'message': '命令发送成功'})
        
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=400)
    except ConnectionError as e:
        return web.json_response({'error': str(e)}, status=500)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def command_endpoint(request):
    """处理/command端点的POST请求"""
    try:
        data = await request.json()
        
        # 检查游戏是否运行
        if not is_game_running():
            return web.json_response({'error': '游戏未运行'}, status=400)
        
        # 将整个JSON对象转发给游戏
        command_str = json.dumps(data)
        await send_to_game_socket(command_str)
        return web.json_response({'status': 'ok', 'message': '命令转发成功'})
        
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=400)
    except ConnectionError as e:
        return web.json_response({'error': str(e)}, status=500)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/index.html", index)
app.router.add_post("/offer", offer)
app.router.add_post("/set_capture_mode", set_capture_mode)
app.router.add_post("/set_resolution", set_resolution)
app.router.add_get("/capture_methods", get_capture_methods)
app.router.add_get("/resolutions", get_resolutions)

# 游戏管理API
app.router.add_post("/start_game", start_game_endpoint)
app.router.add_post("/stop_game", stop_game_endpoint)
app.router.add_get("/game_status", game_status)
app.router.add_post("/send_command", send_command)
app.router.add_post("/command", command_endpoint)

print(f"Server is running on port {port}")
print("游戏转发系统已启动")

# 启动web服务器
async def main():
    # 启动web服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)  # 监听所有网络接口
    await site.start()
    
    print(f"✅ 服务器已启动在 http://0.0.0.0:{port}")
    print("✅ 支持局域网和IPv6连接")
    
    try:
        # 保持运行
        await asyncio.Future()  # 无限等待
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())