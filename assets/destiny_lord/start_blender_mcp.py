# Blender MCP 一键连接脚本。
# 在已打开的 Blender GUI 中运行本文件，会将当前场景的 MCP 服务设置为 9876 端口并立即启动。
import bpy
import importlib
import socket
import time


PORT = 9876


def main():
    """配置并启动 Blender MCP；不保存文件，避免覆盖用户未保存的模型修改。"""
    scene = bpy.context.scene
    scene.blendermcp_port = PORT
    scene.blendermcp_auto_start_server = True

    # 先调用插件操作；若操作未能改变状态，则直接调用已安装的 addon.py 服务类。
    if not scene.blendermcp_server_running:
        bpy.ops.blendermcp.start_server()
        time.sleep(0.2)

    server = getattr(bpy.types, "blendermcp_server", None)
    if server is None or not server.running:
        addon = importlib.import_module("addon")
        server = addon.BlenderMCPServer(host="127.0.0.1", port=PORT)
        bpy.types.blendermcp_server = server
        server.start()
        time.sleep(0.2)

    running = bool(getattr(server, "running", False))
    scene.blendermcp_server_running = running
    if not running:
        raise RuntimeError("MCP 服务未启动；请打开 Blender 的“窗口 → 切换系统控制台”查看报错。")

    # 额外用本机 socket 验证监听结果，避免界面显示启动但端口实际不可用。
    with socket.create_connection(("127.0.0.1", PORT), timeout=1.0):
        pass
    print(f"Blender MCP 状态：已启动，端口：{PORT}")


if __name__ == "__main__":
    main()
