"""
Liquid UI (Self-Morphing Interface)
A dynamic CustomTkinter window that reads from a JSON config file.
If the AI modifies the JSON file, the GUI physically morphs and changes structure in real-time.
"""

import customtkinter as ctk
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ui_config.json")

class LiquidUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x500")
        self.last_modified = 0
        self.build_ui()
        self.check_for_updates()
        
    def build_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "theme": "dark",
                "color": "blue",
                "title": "Ultron Liquid UI",
                "widgets": [{"type": "label", "text": "System Online"}]
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=2)
                
        with open(CONFIG_FILE, "r") as f:
            try:
                config = json.load(f)
            except:
                return # Skip build if JSON is currently being written to
            
        ctk.set_appearance_mode(config.get("theme", "dark"))
        ctk.set_default_color_theme(config.get("color", "blue"))
        self.title(config.get("title", "Ultron Liquid UI"))
        
        for w in config.get("widgets", []):
            if w["type"] == "label":
                lbl = ctk.CTkLabel(self, text=w["text"], font=("Inter", 18, "bold"))
                lbl.pack(pady=15, padx=20)
            elif w["type"] == "button":
                btn = ctk.CTkButton(self, text=w["text"], height=40)
                btn.pack(pady=15, padx=20)
                
        self.last_modified = os.path.getmtime(CONFIG_FILE)

    def check_for_updates(self):
        if os.path.exists(CONFIG_FILE):
            mod_time = os.path.getmtime(CONFIG_FILE)
            if mod_time > self.last_modified:
                print("[Liquid UI] Structural change detected. Morphing interface...")
                self.build_ui()
        self.after(1000, self.check_for_updates)

def start_liquid_ui():
    app = LiquidUI()
    app.mainloop()

if __name__ == "__main__":
    start_liquid_ui()
