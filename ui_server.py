
from flask import Flask, jsonify

app = Flask(__name__)

current_state = "Idle"

def set_state(state):
    global current_state
    current_state = state

@app.route("/state")
def state():
    return jsonify({"state": current_state})

def run_server():
    app.run(port=5000)

