#!/usr/bin/env python3
# Test WebSocket server (stands in for the UAV / a web page).
# Type a key + Enter; the current command is re-sent 10x per second.
import json
import threading
import time

from websocket_server import WebsocketServer

WS_HOST = "localhost"
WS_PORT = 8765
SEND_HZ = 10

#  key: (linear m/s, angular rad/s)
KEYS = {
    "w": (0.5, 0.0),     # forward
    "d": (0.5, 0.3),     # forward + left
    "a": (0.5, -0.3),    # forward + right
    "s": (-0.3, 0.0),    # reverse
    ",": (0.0, 0.0),     # stop
}

def run(host: str, port: int) -> None:
    cmd = [(0.0, 0.0)]   # list so nested callbacks/threads can mutate
    server = WebsocketServer(host=host, port=port)

    def on_new_client(client, server):
        print(f"client connected (id {client['id']})")

    def on_client_left(client, server):
        print("client disconnected")

    def send_thread():
        while True:
            linear, angular = cmd[0]
            msg = {"type": "cmd_vel", "data": {"linear": linear, "angular": angular}}
            server.send_message_to_all(json.dumps(msg))
            time.sleep(1.0 / SEND_HZ)

    server.set_fn_new_client(on_new_client)
    server.set_fn_client_left(on_client_left)

    # Server and sender run in background threads, keyboard on the main thread
    threading.Thread(target=server.run_forever, daemon=True).start()
    threading.Thread(target=send_thread, daemon=True).start()

    print(f"Server on ws://{host}:{port}")
    print("i fwd | u fwd+left | o fwd+right | , reverse | k stop | q quit")
    try:
        while True:
            key = input("key> ").strip()
            if key == "q":
                break
            if key in KEYS:
                cmd[0] = KEYS[key]
            else:
                print("unknown key")
    finally:
        cmd[0] = (0.0, 0.0)
        time.sleep(0.3)   # let the stop go out


if __name__ == "__main__":
    try:
        run(WS_HOST, WS_PORT)
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
