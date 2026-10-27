// Pushed by Copilot, still figuring things out

don't worry about config files or launch files
urdf was taken from a forum (model for gazeebo)


scripts -
          ws_test_server → (WebSocket) → ws_cmd_vel → /cmd_vel → sim_ackermann_bridge → controllers → wheels (gazeebo)
             sender                       receiver                    translator
