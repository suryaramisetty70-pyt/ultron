import sys
import socket
import json
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

class UDPListener(QThread):
    state_received = pyqtSignal(dict)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", 5005))
        sock.settimeout(1.0)
        while True:
            try:
                data, _ = sock.recvfrom(4096)
                message = json.loads(data.decode("utf-8"))
                self.state_received.emit(message)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"HUD UDP Error: {e}")

class UltronHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        self.udp_thread = UDPListener()
        self.udp_thread.state_received.connect(self.update_state)
        self.udp_thread.start()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Position at bottom center
        screen = QApplication.primaryScreen().geometry()
        width, height = 600, 150
        x = (screen.width() - width) // 2
        y = screen.height() - height - 50
        self.setGeometry(x, y, width, height)

        self.layout = QVBoxLayout()
        
        # Status Label (The glowing ring/text)
        self.status_label = QLabel("ULTRON STANDBY")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Consolas", 16, QFont.Bold))
        self.status_label.setStyleSheet("color: #00ffff; text-shadow: 0 0 10px #00ffff;")
        
        # Subtitle Label
        self.subtitle_label = QLabel("")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setFont(QFont("Consolas", 12))
        self.subtitle_label.setStyleSheet("color: #ffffff;")
        self.subtitle_label.setWordWrap(True)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.subtitle_label)
        self.setLayout(self.layout)

        # Timer for adaptive transparency (Fullscreen detection)
        self.transparency_timer = QTimer()
        self.transparency_timer.timeout.connect(self.check_fullscreen_activity)
        self.transparency_timer.start(1000)

    def check_fullscreen_activity(self):
        """Checks if foreground window is fullscreen. If so, lowers opacity."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            screen = QApplication.primaryScreen().geometry()
            # If active window covers the screen, lower HUD opacity
            if width >= screen.width() and height >= screen.height():
                self.setWindowOpacity(0.15)
            else:
                self.setWindowOpacity(0.95)
        except Exception:
            pass

    def update_state(self, message):
        state = message.get("state", "standby")
        text = message.get("text", "")
        
        if state == "listening":
            self.status_label.setText("● LISTENING")
            self.status_label.setStyleSheet("color: #00ff00; background-color: rgba(0, 50, 0, 150); border-radius: 10px; padding: 10px;")
        elif state == "thinking":
            self.status_label.setText("⚙ PROCESSING")
            self.status_label.setStyleSheet("color: #ffff00; background-color: rgba(50, 50, 0, 150); border-radius: 10px; padding: 10px;")
        elif state == "speaking":
            self.status_label.setText("🔊 SPEAKING")
            self.status_label.setStyleSheet("color: #ff0055; background-color: rgba(50, 0, 0, 150); border-radius: 10px; padding: 10px;")
        else:
            self.status_label.setText("VISION STANDBY")
            self.status_label.setStyleSheet("color: #00ffff; background-color: rgba(0, 20, 50, 100); border-radius: 10px; padding: 10px;")
            
        self.subtitle_label.setText(text)
        self.subtitle_label.setStyleSheet("color: white; background-color: rgba(0,0,0,150); padding: 5px; border-radius: 5px;")
        if not text:
            self.subtitle_label.setStyleSheet("background-color: transparent;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = UltronHUD()
    hud.show()
    sys.exit(app.exec_())
