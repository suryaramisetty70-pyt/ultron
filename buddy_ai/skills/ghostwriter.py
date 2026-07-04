"""
Ghostwriter Engine
A transparent, borderless PyQt6 overlay that provides AI-powered text autocomplete 
across any Windows application.
"""
import sys
import threading
import time
import keyboard
import pyautogui
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class GhostwriterOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Make the window transparent, borderless, and always on top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Setup Text Label
        self.label = QLabel("Initializing Ghostwriter...", self)
        self.label.setFont(QFont("Consolas", 14))
        self.label.setStyleSheet("color: rgba(100, 255, 100, 220); background-color: rgba(0, 0, 0, 180); padding: 8px; border-radius: 5px;")
        
        # Position it at the bottom-center of the screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(int(screen.width() / 2) - 300, screen.height() - 150, 600, 60)
        
        self.current_suggestion = ""
        self.is_active = False
        self.hide()

        # Start keyboard listener in a separate thread
        threading.Thread(target=self.listen_for_hotkeys, daemon=True).start()
        print("[Ghostwriter] Engine online. Press Ctrl+Space to predict text.")

    def listen_for_hotkeys(self):
        # Trigger autocomplete on Ctrl+Space
        keyboard.add_hotkey('ctrl+space', self.trigger_autocomplete)
        # Accept suggestion on Tab
        keyboard.add_hotkey('tab', self.accept_suggestion)
        # Cancel suggestion on Esc
        keyboard.add_hotkey('esc', self.cancel_suggestion)
        keyboard.wait()

    def trigger_autocomplete(self):
        if self.is_active:
            return
            
        print("[Ghostwriter] Predicting next sequence...")
        # (Mock LLM prediction - In reality, this queries local Ollama)
        self.current_suggestion = " This is an AI predicted sentence from the Ghostwriter engine."
        
        # Use QTimer to safely update the GUI from the background thread
        QTimer.singleShot(0, self.show_suggestion)

    def accept_suggestion(self):
        if self.is_active:
            print("[Ghostwriter] Suggestion accepted. Typing...")
            QTimer.singleShot(0, self.hide)
            self.is_active = False
            # Wait a tiny bit for the UI to hide before simulating keystrokes
            time.sleep(0.1)
            pyautogui.write(self.current_suggestion, interval=0.01)

    def cancel_suggestion(self):
        if self.is_active:
            print("[Ghostwriter] Suggestion discarded.")
            QTimer.singleShot(0, self.hide)
            self.is_active = False

    def show_suggestion(self):
        self.label.setText(f"Ghostwriter [Press TAB]:{self.current_suggestion}")
        self.label.adjustSize()
        self.show()
        self.is_active = True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = GhostwriterOverlay()
    sys.exit(app.exec())
