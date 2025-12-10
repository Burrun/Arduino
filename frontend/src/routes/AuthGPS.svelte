<script>
    import { onMount, onDestroy } from "svelte";
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle";
    let message = "Waiting for GPS data...";
    let location = null;
    let pollInterval = null;

    async function pollGPS() {
        try {
            const res = await api.getGPS();
            location = res.data.data;
            $authData.gps = location;
            status = "success";
            message = `Location: ${location.latitude}, ${location.longitude}`;
        } catch (e) {
            // Don't show error while waiting for first GPS data
            if (status !== "success") {
                message = "Waiting for GPS data...";
            }
        }
    }

    onMount(() => {
        // Poll GPS every 2 seconds
        pollGPS();
        pollInterval = setInterval(pollGPS, 2000);
    });

    onDestroy(() => {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
    });

    function next() {
        $currentStep = 7; // Go to Signature
    }
</script>

<div class="full-screen column">
    <StepIndicator current={4} />
    <h2 class="title">Location Verification</h2>

    <div class="content center column">
        <div class="map-box">
            {#if location}
                <div class="pin">📍</div>
                <div class="coords">
                    {location.latitude}<br />{location.longitude}
                </div>
            {:else}
                <div class="placeholder">Waiting for GPS...</div>
            {/if}
        </div>
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 5)}>Back</Button>
        {#if status === "success" && location}
            <Button primary onClick={next}>Next</Button>
        {:else}
            <div class="waiting-text">Waiting for GPS signal...</div>
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
        border: 2px solid #445;
    }
    .pin {
        font-size: 3rem;
    }
    .coords {
        margin-top: 10px;
        font-family: monospace;
    }
    .waiting-text {
        color: #888;
        font-style: italic;
    }
</style>
