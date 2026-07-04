import makeWASocket, {
    useMultiFileAuthState
} from "@whiskeysockets/baileys"

import readline from "readline"

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
})

async function connectWhatsApp() {

    const { state, saveCreds } =
        await useMultiFileAuthState("auth_info")

    const sock = makeWASocket({
        auth: state
    })

    sock.ev.on("creds.update", saveCreds)

    if (!sock.authState.creds.registered) {

        rl.question(
            "Enter your WhatsApp number with country code: ",
            async (number) => {

                const code =
                    await sock.requestPairingCode(number)

                console.log("\nYour Pairing Code:")
                console.log(code)
            }
        )
    }

    sock.ev.on("connection.update", ({ connection }) => {

        if (connection === "open") {

            console.log("✅ WhatsApp Connected Successfully")
        }
    })
}

connectWhatsApp()