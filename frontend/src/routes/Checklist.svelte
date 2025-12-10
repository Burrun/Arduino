<script>
    import { onMount } from "svelte";
    import Button from "../lib/Button.svelte";
    import { currentStep, sensorStatus } from "../lib/store";
    import { api } from "../lib/api";

    let checking = true;
    let error = null;
    let hasFailed = false;

    onMount(async () => {
        try {
            // Check all sensors using the new status endpoint
            const response = await fetch("/api/sensors/status");
            if (!response.ok) {
                throw new Error("Failed to check sensors");
            }

            const status = await response.json();

            // Update sensor status
            $sensorStatus.rtc = status.rtc;
            $sensorStatus.fingerprint = status.fingerprint;
            $sensorStatus.camera = status.camera;
            $sensorStatus.gps = status.gps;
            $sensorStatus.signature = status.signature;

            // Check if any sensor failed
            hasFailed =
                !status.rtc ||
                !status.fingerprint ||
                !status.camera ||
                !status.gps;

            if (hasFailed) {
                error = "One or more sensors failed. Please check connections.";
            }

            checking = false;
        } catch (e) {
            error = "Failed to connect to sensors. Ensure backend is running.";
            checking = false;
            hasFailed = true;
        }
    });

    function next() {
        $currentStep = 3; // Go to Auth Steps
    }
</script>

<div class="full-screen column">
    <h2 class="title">System Check</h2>

    <div class="content">
        {#if error}
            <div class="error">{error}</div>
        {/if}

        <div class="grid">
            <div
                class="item"
                class:ok={$sensorStatus.rtc}
                class:failed={!checking && !$sensorStatus.rtc}
            >
                RTC Clock
            </div>
            <div
                class="item"
                class:ok={$sensorStatus.fingerprint}
                class:failed={!checking && !$sensorStatus.fingerprint}
            >
                Fingerprint
            </div>
            <div
                class="item"
                class:ok={$sensorStatus.camera}
                class:failed={!checking && !$sensorStatus.camera}
            >
                Camera
            </div>
            <div
                class="item"
                class:ok={$sensorStatus.gps}
                class:failed={!checking && !$sensorStatus.gps}
            >
                GPS
            </div>
            <div class="item" class:ok={!checking}>News OTP</div>
            <div
                class="item"
                class:ok={$sensorStatus.signature}
                class:failed={!checking && !$sensorStatus.signature}
            >
                Signature
            </div>
        </div>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 1)}>Back</Button>
        <Button primary disabled={checking || hasFailed} onClick={next}>
            {checking ? "Checking..." : "Continue"}
        </Button>
    </div>
</div>

<style>
    .grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
        margin-top: 20px;
    }
    .item {
        background: #333;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #555;
    }
    .item.ok {
        border-left-color: #4caf50;
        background: #2e3b2f;
    }
    .item.failed {
        border-left-color: #f44336;
        background: #3d2222;
    }
    .error {
        color: #ff4444;
        background: #3d2222;
        padding: 10px;
        border-radius: 4px;
    }
</style>
