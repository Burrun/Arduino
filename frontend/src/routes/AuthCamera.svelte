<script>
    import { onMount } from "svelte";
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData, sensorStatus, logId } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle";
    let message = "Camera ready! Click to capture and verify.";
    let countdown = 0;

    // Check if camera was verified in Checklist
    $: isCameraReady = $sensorStatus.camera;

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
            // This API call captures image and sends to AuthBox for verification
            const res = await api.verifyFace();
            $authData.camera = true;
            status = "success";
            message = "Face verification complete!";
        } catch (e) {
            status = "error";
            message =
                e.response?.data?.detail || "Verification failed. Try again.";
        }
    }

    function next() {
        $currentStep = 5; // Go to Quiz
    }

    onMount(() => {
        if (!isCameraReady) {
            message = "Camera not available. Please check System Check.";
        }
    });
</script>

<div class="full-screen column">
    <StepIndicator current={2} />
    <h2 class="title">Face Authentication</h2>

    <div class="content center column">
        <div
            class="camera-box"
            class:ready={isCameraReady}
            class:success={status === "success"}
        >
            {#if status === "success"}
                <div class="placeholder success-text">✓ Photo Captured</div>
            {:else if status === "capturing"}
                <div class="placeholder capturing-text">
                    {#if countdown > 0}
                        <span class="countdown">{countdown}</span>
                    {:else}
                        Processing...
                    {/if}
                </div>
            {:else if isCameraReady}
                <div class="placeholder ready-text">📷 Camera Ready</div>
            {:else}
                <div class="placeholder">Camera not available</div>
            {/if}
        </div>
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 3)}>Back</Button>
        {#if status !== "success"}
            <Button
                primary
                onClick={captureAndVerify}
                disabled={status === "capturing" || !isCameraReady}
            >
                {status === "capturing" ? message : "Capture & Verify"}
            </Button>
        {:else}
            <Button primary onClick={next}>Next</Button>
        {/if}
    </div>
</div>

<style>
    .content {
        padding-top: 5px !important;
        justify-content: flex-start !important;
    }
    .camera-box {
        width: 550px;
        height: 400px;
        background: #000;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 3px solid #555;
        transition: border-color 0.3s ease;
    }
    .camera-box.ready {
        border-color: #4ade80;
        box-shadow: 0 0 15px rgba(74, 222, 128, 0.3);
    }
    .camera-box.success {
        border-color: #22c55e;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
    }
    .placeholder {
        color: #666;
    }
    .ready-text {
        color: #4ade80;
        font-size: 1.2rem;
    }
    .success-text {
        color: #22c55e;
        font-size: 1.3rem;
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
