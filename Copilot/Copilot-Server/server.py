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
    {"name": "测试帧", "desc": "彩色测试帧", "arg": None},
]
capture_method_index = 0  # 默认使用第一个方法

class ScreenTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        global capture_method_index
        method = CAPTURE_METHODS[capture_method_index]
        print(f"当前捕获方法: {method['name']} - {method['desc']}")
        
        if method["arg"] is None:
            # 使用测试帧
            self.cap = None
            self.temp_file = None
            print("使用测试帧模式")
        elif method["arg"] == "screencapture":
            # 使用 screencapture 方法
            self.cap = None
            self.temp_file = None
            self.setup_screencapture()
        elif isinstance(method["arg"], int):
            # 摄像头
            self.cap = cv2.VideoCapture(method["arg"])
            self.temp_file = None
            if self.cap and self.cap.isOpened():
                print(f"✅ 摄像头 {method['arg']} 打开成功")
            else:
                print(f"❌ 摄像头 {method['arg']} 打开失败，使用测试帧")
                self.cap = None
    
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
                frame = cv2.resize(frame, (1280, 720))
            else:
                # 如果读取失败，创建测试帧
                frame = self.create_test_frame()
        elif self.temp_file and self.temp_file.name.endswith('.png'):
            # 使用 screencapture
            try:
                current_time = time.time()
                if not hasattr(self, 'last_capture_time') or current_time - self.last_capture_time > 1:  # 每秒截图一次
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
                        frame = cv2.resize(frame, (1280, 720))
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

        pc.addTrack(ScreenTrack())

        # 创建 RTCSessionDescription 对象
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    
    except Exception as e:
        print(f"Error in offer handler: {e}")
        print(traceback.format_exc())
        return web.json_response({"error": str(e)}, status=500)

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

async def get_capture_methods(request):
    """获取所有可用的捕获方法"""
    try:
        methods = [{"index": i, "name": method["name"]} for i, method in enumerate(CAPTURE_METHODS)]
        return web.json_response({"methods": methods, "current_index": capture_method_index})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/index.html", index)
app.router.add_post("/offer", offer)
app.router.add_post("/set_capture_mode", set_capture_mode)
app.router.add_get("/capture_methods", get_capture_methods)

# 启动前检查设备
list_video_devices()

print(f"Server is running on port {port}")
web.run_app(app, port=port)