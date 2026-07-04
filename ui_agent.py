
import tkinter as tk
import threading
import time

state = "Idle"

def set_state(new_state):
    global state
    state = new_state

def start_ui():

    root = tk.Tk()
    root.title("Buddy AI")
    root.geometry("300x300")
    root.configure(bg="black")
    root.attributes("-topmost", True)

    canvas = tk.Canvas(root, width=300, height=300, bg="black", highlightthickness=0)
    canvas.pack()

    text = canvas.create_text(150, 250, text="Idle", fill="cyan", font=("Helvetica", 16))
    circle = canvas.create_oval(100, 100, 200, 200, outline="cyan", width=3)

    pulse = 0

    def animate():
        nonlocal pulse
        while True:

            if state == "Listening":
                color = "green"
            elif state == "Thinking":
                color = "yellow"
            elif state == "Speaking":
                color = "cyan"
            else:
                color = "gray"

            pulse = (pulse + 2) % 20

            canvas.coords(circle, 100-pulse, 100-pulse, 200+pulse, 200+pulse)
            canvas.itemconfig(circle, outline=color)
            canvas.itemconfig(text, text=state)

            time.sleep(0.05)

    threading.Thread(target=animate, daemon=True).start()

    root.mainloop()

