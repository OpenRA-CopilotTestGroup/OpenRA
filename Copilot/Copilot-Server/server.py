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

class ScreenTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        # 尝试多种视频捕获方法
        self.cap = None
        self.setup_capture()
    
    def setup_capture(self):
        """设置视频捕获，尝试多种方法"""
        capture_methods = [
            # 方法1: 使用默认设备
            lambda: cv2.VideoCapture(0),
            # 方法2: 使用 FFMPEG 和 avfoundation
            lambda: cv2.VideoCapture("ffmpeg -f avfoundation -framerate 15 -video_size 1280x720 -i 0:none -pix_fmt bgr0 -vcodec rawvideo -f rawvideo -", cv2.CAP_FFMPEG),
            # 方法3: 使用 FFMPEG 和不同的设备索引
            lambda: cv2.VideoCapture("ffmpeg -f avfoundation -framerate 15 -video_size 1280x720 -i 1:none -pix_fmt bgr0 -vcodec rawvideo -f rawvideo -", cv2.CAP_FFMPEG),
            # 方法4: 使用 FFMPEG 和屏幕捕获
            lambda: cv2.VideoCapture("ffmpeg -f avfoundation -framerate 15 -video_size 1280x720 -i 1 -pix_fmt bgr0 -vcodec rawvideo -f rawvideo -", cv2.CAP_FFMPEG),
        ]
        
        for i, method in enumerate(capture_methods):
            try:
                print(f"尝试视频捕获方法 {i+1}...")
                self.cap = method()
                if self.cap.isOpened():
                    print(f"视频捕获方法 {i+1} 成功")
                    return
                else:
                    self.cap.release()
            except Exception as e:
                print(f"视频捕获方法 {i+1} 失败: {e}")
                if self.cap:
                    self.cap.release()
        
        # 如果所有方法都失败，创建一个测试帧
        print("所有视频捕获方法都失败，使用测试帧")
        self.cap = None

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (1280, 720))
            else:
                # 如果读取失败，创建测试帧
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

pcs = set()

async def offer(request):
    try:
        params = await request.json()
        
        # 验证参数
        if "sdp" not in params or "type" not in params:
            return web.json_response({"error": "Missing sdp or type parameter"}, status=400)
        
        pc = RTCPeerConnection()
        pcs.add(pc)

        # 添加视频轨道
        track = ScreenTrack()
        pc.addTrack(track)

        # 创建 RTCSessionDescription 对象
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        await pc.setRemoteDescription(offer)
        
        # 创建 answer
        answer = await pc.createAnswer()
        
        # 设置本地描述
        await pc.setLocalDescription(answer)

        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    
    except Exception as e:
        print(f"Error in offer handler: {e}")
        print(traceback.format_exc())
        
        # 清理连接
        try:
            if 'pc' in locals():
                await pc.close()
                pcs.discard(pc)
        except:
            pass
            
        return web.json_response({"error": str(e)}, status=500)

async def index(request):
    response = web.FileResponse("index.html")
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

async def cleanup(request):
    """清理所有连接"""
    try:
        for pc in list(pcs):
            pc.close()
        pcs.clear()
        return web.json_response({"status": "success", "message": "All connections cleaned up"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/index.html", index)
app.router.add_post("/offer", offer)
app.router.add_post("/cleanup", cleanup)

# 启动前检查设备
list_video_devices()

print(f"Server is running on port {port}")
web.run_app(app, port=port)