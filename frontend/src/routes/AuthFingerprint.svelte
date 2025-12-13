<script>
    import { onMount } from "svelte";
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData, sensorStatus, logId } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle"; // idle, scanning, success, error
    let message = "Place your finger on the sensor";
    let countdown = 30;
    let intervalId = null;

    // Check if fingerprint was verified in Checklist
    $: isFingerprintReady = $sensorStatus.fingerprint;

    async function scanAndVerify() {
        status = "scanning";
        message = "Scanning... Please keep your finger still";
        countdown = 30;

        // Start countdown
        intervalId = setInterval(() => {
            countdown--;
            if (countdown <= 0) {
                clearInterval(intervalId);
            }
        }, 1000);

        try {
            // This API call captures fingerprint and sends to AuthBox for verification
            const res = await api.verifyFingerprint();
            $authData.fingerprint = true;
            status = "success";
            message = "Fingerprint verification complete!";
            clearInterval(intervalId);
        } catch (e) {
            status = "error";
            message = e.response?.data?.detail || "Scan failed. Try again.";
            clearInterval(intervalId);
        }
    }

    function next() {
        $currentStep = 4; // Go to Camera
    }

    onMount(() => {
        if (!isFingerprintReady) {
            message =
                "Fingerprint sensor not available. Please check System Check.";
        }
    });
</script>

<div class="full-screen column">
    <StepIndicator current={1} />
    <h2 class="title">Fingerprint Authentication</h2>

    <div class="content center column">
        <div
            class="icon-box"
            class:ready={isFingerprintReady && status === "idle"}
            class:success={status === "success"}
            class:error={status === "error"}
        >
            <span class="icon">👆</span>
            {#if status === "scanning" && countdown > 0}
                <div class="countdown">{countdown}s</div>
            {/if}
        </div>
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 2)}>Back</Button>
        {#if status !== "success"}
            <Button
                primary
                onClick={scanAndVerify}
                disabled={status === "scanning" || !isFingerprintReady}
            >
                {status === "scanning" ? "Scanning..." : "Scan & Verify"}
            </Button>
        {:else}
            <Button primary onClick={next}>Next</Button>
        {/if}
    </div>
</div>

<style>
    .icon-box {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: #333;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        font-size: 3rem;
        border: 4px solid #555;
    }
    .icon-box.success {
        border-color: #4caf50;
        background: #2e3b2f;
    }
    .icon-box.error {
        border-color: #ff4444;
        background: #3d2222;
    }
    .status-text {
        font-size: 1.2rem;
    }
</style>
