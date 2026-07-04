javascript
async function updateState() {
    try {
        const res = await fetch("http://127.0.0.1:5000/state");
        const data = await res.json();

        document.getElementById("status").innerText = data.state;

        let circle = document.getElementById("circle");

        if (data.state === "Listening") {
            circle.style.borderColor = "green";
        } else if (data.state === "Thinking") {
            circle.style.borderColor = "yellow";
        } else if (data.state === "Speaking") {
            circle.style.borderColor = "cyan";
        } else {
            circle.style.borderColor = "gray";
        }

    } catch (e) {
        console.log("Server not running");
    }
}

setInterval(updateState, 500);

