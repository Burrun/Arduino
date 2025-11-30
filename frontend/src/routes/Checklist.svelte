<script>
    import { onMount } from "svelte";
    import Button from "../lib/Button.svelte";
    import { currentStep, sensorStatus } from "../lib/store";
    import { api } from "../lib/api";

    let checking = true;
    let error = null;

    onMount(async () => {
        try {
            // Check RTC
            await api.getRTC();
            $sensorStatus.rtc = true;

            // Simulate other checks (since we don't have endpoints for status yet)
            setTimeout(() => {
                $sensorStatus.fingerprint = true;
                $sensorStatus.camera = true;
                $sensorStatus.gps = true;
                $sensorStatus.signature = true;
                checking = false;
            }, 1500);
        } catch (e) {
            error = "Failed to connect to sensors. Ensure backend is running.";
            checking = false;
        }
    });

    function next() {
        $currentStep = 2; // Go to Auth Steps
    }
</script>

<div class="full-screen column">
    <h2 class="title">System Check</h2>

    <div class="content">
        {#if error}
            <div class="error">{error}</div>
        {/if}

        <div class="grid">
            <div class="item" class:ok={$sensorStatus.rtc}>RTC Clock</div>
            <div class="item" class:ok={$sensorStatus.fingerprint}>
                Fingerprint
            </div>
            <div class="item" class:ok={$sensorStatus.camera}>Camera</div>
            <div class="item" class:ok={$sensorStatus.gps}>GPS</div>
            <div class="item" class:ok={$sensorStatus.signature}>Signature</div>
        </div>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 0)}>Back</Button>
        <Button primary disabled={checking || error} onClick={next}>
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
    .error {
        color: #ff4444;
        background: #3d2222;
        padding: 10px;
        border-radius: 4px;
    }
</style>
