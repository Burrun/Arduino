<script>
    import { onMount } from "svelte";
    import { currentStep, logs, addLog } from "../lib/store";

    onMount(() => {
        addLog("Initiating secure transfer...");
        setTimeout(() => addLog("Encrypting biometric data..."), 1000);
        setTimeout(() => addLog("Connecting to bank server..."), 2000);
        setTimeout(() => addLog("Uploading fingerprint... OK"), 3000);
        setTimeout(() => addLog("Uploading signature... OK"), 4000);
        setTimeout(() => addLog("Verifying transaction... OK"), 5000);

        setTimeout(() => {
            $currentStep = 9; // Go to Result
        }, 6000);
    });
</script>

<div class="full-screen center column">
    <h2 class="title">Sending Data</h2>

    <div class="loader"></div>

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
</style>
