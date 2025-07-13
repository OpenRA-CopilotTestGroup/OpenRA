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

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=8080)
args = parser.parse_args()
port = args.port

def list_video_devices():
    """列出可用的视频设备"""
    print("=== 检查可用的视频设备 ===")
    
    # 检查 OpenCV 可用的设备
    print("OpenCV 设备:")
    for i in range(10):  # 检查前10个设备
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"  设备 {i}: 可用")
            cap.release()
        else:
            cap.release()
    
    # 检查 FFmpeg 设备 (macOS)
    try:
        result = subprocess.run(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("\nFFmpeg avfoundation 设备:")
            for line in result.stderr.split('\n'):
                if 'video' in line.lower() or 'camera' in line.lower():
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"无法检查 FFmpeg 设备: {e}")

# 捕获方法列表
CAPTURE_METHODS = [
    {"name": "摄像头0", "desc": "MacBook Pro Camera", "arg": 0},
    {"name": "摄像头1", "desc": "kamico Camera", "arg": 1},
    {"name": "屏幕截图", "desc": "Screen capture (screencapture)", "arg": "screencapture"},
    {"name": "屏幕截图智能", "desc": "Smart screen capture", "arg": "smart_screencapture"},
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

class ScreenCapture:
    """统一的屏幕捕获类"""
    def __init__(self, mode="normal", target_width=1280, target_height=720):
        self.mode = mode  # "normal" 或 "smart"
        self.target_width = target_width
        self.target_height = target_height
        self.temp_file = None
        
        # 智能模式特有属性
        if mode == "smart":
            self.max_fps = 30
            self.min_fps = 5
            self.current_fps = 15
            self.frame_history = deque(maxlen=10)
            self.network_quality = 1.0
            self.motion_threshold = 0.02
        
        self.last_frame = None
        self.last_capture_time = 0
        self.setup_temp_file()
    
    def setup_temp_file(self):
        """设置临时文件"""
        try:
            self.temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.temp_file.close()
            print(f"✅ 屏幕捕获临时文件创建成功: {self.temp_file.name}")
        except Exception as e:
            print(f"❌ 屏幕捕获临时文件创建失败: {e}")
            self.temp_file = None
    
    def update_resolution(self, width, height):
        """更新目标分辨率"""
        self.target_width = width
        self.target_height = height
        print(f"✅ 分辨率已更新为: {width}x{height}")
    
    def update_network_quality(self, quality):
        """更新网络质量指标（仅智能模式）"""
        if self.mode == "smart":
            self.network_quality = max(0.1, min(1.0, quality))
            print(f"网络质量更新: {self.network_quality:.2f}")
    
    def calculate_frame_difference(self, frame1, frame2):
        """计算两帧之间的差异（仅智能模式）"""
        if frame1 is None or frame2 is None:
            return 1.0
        
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        mean_diff = np.mean(diff) / 255.0
        
        return mean_diff
    
    def detect_motion(self, current_frame):
        """检测运动（仅智能模式）"""
        if self.mode != "smart" or len(self.frame_history) < 2:
            return True
        
        last_frame = self.frame_history[-1]
        motion_level = self.calculate_frame_difference(last_frame, current_frame)
        return motion_level > self.motion_threshold
    
    def adjust_fps_based_on_motion(self, has_motion):
        """根据运动情况调整帧率（仅智能模式）"""
        if self.mode != "smart":
            return
        
        if has_motion:
            target_fps = int(self.max_fps * self.network_quality)
            self.current_fps = max(self.min_fps, min(self.max_fps, target_fps))
        else:
            self.current_fps = max(self.min_fps, self.current_fps // 2)
    
    def capture_frame(self):
        """捕获一帧"""
        if not self.temp_file:
            return None
        
        current_time = time.time()
        
        # 智能模式的帧率控制
        if self.mode == "smart":
            frame_interval = 1.0 / self.current_fps
            if current_time - self.last_capture_time < frame_interval and self.last_frame is not None:
                return self.last_frame
        
        # 普通模式的固定间隔控制
        elif self.mode == "normal":
            frame_interval = 0.1  # 每秒10次
            if current_time - self.last_capture_time < frame_interval:
                return self.last_frame
        
        try:
            # 截图
            cmd = ['screencapture', '-x', self.temp_file.name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0 and os.path.exists(self.temp_file.name):
                frame = cv2.imread(self.temp_file.name)
                if frame is not None:
                    # 智能模式的处理
                    if self.mode == "smart":
                        has_motion = self.detect_motion(frame)
                        self.adjust_fps_based_on_motion(has_motion)
                        self.frame_history.append(frame.copy())
                        
                        if has_motion:
                            print(f"检测到运动，帧率: {self.current_fps}fps")
                    
                    # 更新状态
                    self.last_frame = frame
                    self.last_capture_time = current_time
                    return frame
                else:
                    print("❌ 读取截图失败")
            else:
                print(f"❌ 截图命令失败: {result.stderr}")
        except Exception as e:
            print(f"屏幕捕获异常: {e}")
        
        # 如果捕获失败但有上一帧，返回上一帧
        if self.last_frame is not None:
            return self.last_frame
        
        return None
    
    def cleanup(self):
        """清理资源"""
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
                print(f"临时文件 {self.temp_file.name} 已删除")
                print("traceback:")
                print(traceback.format_exc())
            except Exception as e:
                print(f"删除临时文件失败: {e}")
            self.temp_file = None

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
            self.screen_capture = None
            self.target_width = resolution['width']
            self.target_height = resolution['height']
            print("使用测试帧模式")
        elif method["arg"] == "screencapture":
            # 使用普通屏幕捕获
            self.cap = None
            self.screen_capture = ScreenCapture(
                mode="normal",
                target_width=resolution['width'], 
                target_height=resolution['height']
            )
            print("✅ 普通屏幕捕获初始化成功")
        elif method["arg"] == "smart_screencapture":
            # 使用智能屏幕捕获
            self.cap = None
            self.screen_capture = ScreenCapture(
                mode="smart",
                target_width=resolution['width'], 
                target_height=resolution['height']
            )
            print("✅ 智能屏幕捕获初始化成功")
        elif isinstance(method["arg"], int):
            # 摄像头
            self.cap = cv2.VideoCapture(method["arg"])
            self.screen_capture = None
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
        if self.screen_capture:
            self.screen_capture.update_resolution(width, height)
        print(f"✅ 视频轨道分辨率已更新为: {width}x{height}")

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
        elif self.screen_capture:
            # 使用统一的屏幕捕获
            frame = self.screen_capture.capture_frame()
            if frame is not None:
                # 保持宽高比的resize
                frame = self.resize_with_aspect_ratio(frame, max_width=self.target_width, max_height=self.target_height)
            else:
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
        print("stop")
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.screen_capture:
            self.screen_capture.cleanup()

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
                    if hasattr(video_track, 'screen_capture') and video_track.screen_capture:
                        video_track.screen_capture.update_network_quality(network_quality)
                    
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
                method = CAPTURE_METHODS[capture_method_index]
                print(f"捕获方法已切换为: {method['name']} - {method['desc']}")
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

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/index.html", index)
app.router.add_post("/offer", offer)
app.router.add_post("/set_capture_mode", set_capture_mode)
app.router.add_post("/set_resolution", set_resolution)
app.router.add_get("/capture_methods", get_capture_methods)
app.router.add_get("/resolutions", get_resolutions)

# 启动前检查设备
list_video_devices()

print(f"Server is running on port {port}")
web.run_app(app, port=port)