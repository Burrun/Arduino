<script>
    import { onMount } from "svelte";
    import { currentStep, authData, logId, logs, addLog } from "../lib/store";
    import { api } from "../lib/api";

    let error = null;

    onMount(async () => {
        addLog("Starting to send verification data...");

        try {
            addLog("Connecting to server...");
            await new Promise((r) => setTimeout(r, 1000));

            addLog("Requesting email send...");
            const res = await api.sendMail($authData.senderEmail);

            if (res.data.isSuccess) {
                addLog(`Email sent successfully: ${res.data.targetMail}`);
                addLog("All verification completed!");

                await new Promise((r) => setTimeout(r, 1500));
                $currentStep = 11; // Go to Result
            } else {
                throw new Error(res.data.message || "Email send failed");
            }
        } catch (e) {
            console.error("Mail error:", e);
            addLog(`Error: ${e.message || "Send failed"}`);
            error = e.message || "Send failed";
        }
    });
</script>

<div class="full-screen center column">
    <h2 class="title">Sending Result</h2>

    {#if !error}
        <div class="loader"></div>
    {:else}
        <p class="error">{error}</p>
        <button class="retry-btn" on:click={() => location.reload()}
            >Retry</button
        >
    {/if}

    <div class="log-window">
        {#each $logs as log}
            <div class="log-line">{log}</div>
        {/each}
    </div>
</div>

<style>
    .loader {
        width: 50px;
        height: 50px;
        border: 5px solid #333;
        border-top-color: #646cff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 30px;
    }
    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
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
    }
    .log-line {
        margin-bottom: 5px;
    }
    .error {
        color: #ff6b6b;
        font-size: 1.2rem;
        margin: 20px 0;
    }
    .retry-btn {
        padding: 10px 20px;
        background: #646cff;
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1rem;
    }
</style>
