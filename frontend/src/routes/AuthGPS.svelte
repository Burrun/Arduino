<script>
    import { onMount } from "svelte";
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData, sensorStatus, logId } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle";
    let message = "GPS ready! Click to capture and verify.";
    let countdown = 0;

    // Check if GPS was verified in Checklist
    $: isGPSReady = $sensorStatus.gps;

    async function captureAndVerify() {
        status = "capturing";
        countdown = 5;
        message = `Capturing in ${countdown} seconds...`;

        // Countdown display
        const countdownInterval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                message = `Capturing in ${countdown} seconds...`;
            } else {
                message = "Verifying with server...";
                clearInterval(countdownInterval);
            }
        }, 1000);

        try {
            // This API call captures GPS and sends to AuthBox for verification
            const res = await api.verifyGPS(0, 0); // Server will capture GPS if lat/lon are 0
            $authData.gps = true;
            status = "success";
            message = "GPS verification complete!";
        } catch (e) {
            status = "error";
            message =
                e.response?.data?.detail || "Verification failed. Try again.";
        }
    }

    function next() {
        $currentStep = 7; // Go to Signature
    }

    onMount(() => {
        if (!isGPSReady) {
            message = "GPS not available. Please check System Check.";
        }
    });
</script>

<div class="full-screen column">
    <StepIndicator current={4} />
    <h2 class="title">Location Verification</h2>

    <div class="content center column">
        <div
            class="map-box"
            class:ready={isGPSReady}
            class:success={status === "success"}
        >
            {#if status === "success"}
                <div class="pin">📍</div>
                <div class="coords success-text">Verified!</div>
            {:else if status === "capturing"}
                <div class="capturing-text">
                    {#if countdown > 0}
                        <span class="countdown">{countdown}</span>
                    {:else}
                        Processing...
                    {/if}
                </div>
            {:else if isGPSReady}
                <div class="ready-text">🛰️ GPS Ready</div>
            {:else}
                <div class="placeholder">GPS not available</div>
            {/if}
        </div>
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 5)}>Back</Button>
        {#if status !== "success"}
            <Button
                primary
                onClick={captureAndVerify}
                disabled={status === "capturing" || !isGPSReady}
            >
                {status === "capturing" ? message : "Capture & Verify"}
            </Button>
        {:else}
            <Button primary onClick={next}>Next</Button>
        {/if}
    </div>
</div>

<style>
    .map-box {
        width: 500px;
        height: 280px;
        background: #223;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 3px solid #445;
        transition: border-color 0.3s ease;
    }
    .map-box.ready {
        border-color: #4ade80;
        box-shadow: 0 0 15px rgba(74, 222, 128, 0.3);
    }
    .map-box.success {
        border-color: #22c55e;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
    }
    .pin {
        font-size: 3rem;
    }
    .coords {
        margin-top: 10px;
        font-family: monospace;
    }
    .placeholder {
        color: #888;
    }
    .ready-text {
        color: #4ade80;
        font-size: 1.2rem;
    }
    .success-text {
        color: #22c55e;
    }
    .capturing-text {
        color: #fbbf24;
        font-size: 1.2rem;
    }
    .countdown {
        font-size: 3rem;
        font-weight: bold;
    }
    .status-text {
        margin-top: 5px;
    }
</style>
