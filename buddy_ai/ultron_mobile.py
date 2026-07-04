from flask import Flask, render_template_string, request, jsonify
import subprocess
import threading
import os
import socket

app = Flask(__name__)

# Iron Man styled HUD for mobile
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultron Mobile Uplink</title>
    <style>
        body {
            background-color: #0a0a1a;
            color: #00ffff;
            font-family: 'Courier New', Courier, monospace;
            text-align: center;
            padding: 20px;
            margin: 0;
            overflow: hidden;
        }
        h1 {
            font-size: 24px;
            text-transform: uppercase;
            letter-spacing: 3px;
            border-bottom: 2px solid #00ffff;
            padding-bottom: 10px;
            text-shadow: 0 0 10px #00ffff;
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-top: 40px;
        }
        .btn {
            background: rgba(0, 255, 255, 0.1);
            border: 1px solid #00ffff;
            color: #00ffff;
            padding: 15px;
            font-size: 18px;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.2);
        }
        .btn:active {
            background: #00ffff;
            color: #000;
            box-shadow: 0 0 20px #00ffff;
        }
        .status {
            margin-top: 40px;
            font-size: 12px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <h1>Ultron Mobile Uplink</h1>
    <p>ARC REACTOR STATUS: ONLINE</p>
    
    <div class="container">
        <button class="btn" onclick="sendCommand('open_notepad')">Initialize Notepad</button>
        <button class="btn" onclick="sendCommand('open_calc')">Initialize Calculator</button>
        <button class="btn" onclick="sendCommand('open_browser')">Access Global Network</button>
        <button class="btn" onclick="sendCommand('sleep_pc')" style="border-color: #ff0000; color: #ff0000;">Lock System</button>
    </div>
    
    <div class="status" id="log">Awaiting command...</div>

    <script>
        function sendCommand(cmd) {
            document.getElementById('log').innerText = 'Transmitting: ' + cmd + '...';
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({command: cmd})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('log').innerText = 'Status: ' + data.status;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/command', methods=['POST'])
def command():
    data = request.json
    cmd = data.get('command')
    
    if cmd == 'open_notepad':
        subprocess.Popen("notepad.exe")
        return jsonify({"status": "Notepad launched successfully."})
    elif cmd == 'open_calc':
        subprocess.Popen("calc.exe")
        return jsonify({"status": "Calculator launched successfully."})
    elif cmd == 'open_browser':
        try:
            os.startfile("chrome.exe")
        except:
            pass
        return jsonify({"status": "Browser launched successfully."})
    elif cmd == 'sleep_pc':
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return jsonify({"status": "System Locked."})
        
    return jsonify({"status": "Unknown command."})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class UltronMobileUplink(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        
    def run(self):
        ip = get_local_ip()
        print(f"\n=========================================")
        print(f"[Ultron] Mobile Uplink Active!")
        print(f"[Ultron] Type this exactly into your phone browser:")
        print(f"         http://{ip}:5000")
        print(f"=========================================\n")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    mobile = UltronMobileUplink()
    mobile.start()
    mobile.join()
