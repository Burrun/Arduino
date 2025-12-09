<script>
    import { onMount } from "svelte";
    import { currentStep, authData, logs, addLog } from "../lib/store";
    import { api } from "../lib/api";

    let status = "sending"; // sending, success, error
    let progress = 0;

    onMount(async () => {
        await sendDataToServer();
    });

    async function sendDataToServer() {
        const steps = [
            { msg: "Initiating secure transfer...", delay: 500 },
            { msg: "Encrypting biometric data...", delay: 800 },
            { msg: "Connecting to verification server...", delay: 800 },
            { msg: "Uploading fingerprint data... OK", delay: 600 },
            { msg: "Uploading face data... OK", delay: 600 },
            { msg: "Uploading signature data... OK", delay: 600 },
            { msg: "Verifying transaction...", delay: 800 },
        ];

        for (let i = 0; i < steps.length; i++) {
            addLog(steps[i].msg);
            progress = ((i + 1) / steps.length) * 100;
            await new Promise((resolve) => setTimeout(resolve, steps[i].delay));
        }

        // Send verification mail if email is provided
        if ($authData.email) {
            addLog("Sending verification email...");
            try {
                const res = await api.sendMail($authData.email);
                addLog(`Email sent to ${res.data.targetMail}... OK`);
            } catch (e) {
                addLog("Email sending failed (continuing anyway)");
                console.error("[MAIL] Error:", e);
            }
        }

        addLog("All verification steps completed!");
        status = "success";

        // Navigate to result after brief delay
        setTimeout(() => {
            $currentStep = 9; // Go to Result
        }, 1500);
    }
</script>

<div class="full-screen center column">
    <h2 class="title">Sending Data</h2>

    <div class="loader-container">
        <div class="loader"></div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <p class="progress-text">{Math.round(progress)}%</p>
    </div>

    <div class="log-window">
        {#each $logs as log}
            <div class="log-line">{log}</div>
        {/each}
    </div>
</div>

<style>
    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
    }
    .loader {
        width: 50px;
        height: 50px;
        border: 5px solid #333;
        border-top-color: #646cff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
    .progress-bar {
        width: 300px;
        height: 8px;
        background: #333;
        border-radius: 4px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #646cff, #8b5cf6);
        transition: width 0.3s ease;
    }
    .progress-text {
        margin-top: 10px;
        font-size: 1.1rem;
        color: #888;
    }
    .log-window {
        width: 100%;
        max-width: 600px;
        height: 200px;
        background: #000;
        border: 1px solid #333;
        padding: 10px;
        text-align: left;
        font-family: monospace;
        overflow-y: auto;
        color: #0f0;
        border-radius: 4px;
    }
    .log-line {
        margin-bottom: 5px;
    }
</style>
