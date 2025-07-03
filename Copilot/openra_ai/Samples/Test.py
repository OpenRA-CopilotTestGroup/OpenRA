from OpenRA_Copilot_Library import GameAPI

# 检查服务器是否运行
if GameAPI.is_server_running():
    print("服务器已启动，可以连接！")
else:
    print("服务器未启动或无法访问，请启动游戏服务器")

# 使用自定义地址和端口
if GameAPI.is_server_running(host="192.168.1.100", port=8080, timeout=1.0):
    print("远程服务器可访问")
