<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle";
    let message = "Acquiring GPS signal...";
    let location = null;

    async function getLocation() {
        status = "scanning";
        message = "Triangulating...";
        try {
            const res = await api.getGPS();
            location = res.data.data;
            $authData.gps = location;
            status = "success";
            message = `Location found: ${location.latitude}, ${location.longitude}`;
        } catch (e) {
            status = "error";
            message = "GPS signal lost. Try again.";
        }
    }

    function next() {
        $currentStep = 6; // Go to Signature
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
        <Button onClick={() => ($currentStep = 4)}>Back</Button>
        {#if status !== "success"}
            <Button
                primary
                onClick={getLocation}
                disabled={status === "scanning"}
            >
                {status === "scanning" ? "Locating..." : "Get Location"}
            </Button>
        {:else}
            <Button primary onClick={next}>Next</Button>
        {/if}
    </div>
</div>

<style>
    .map-box {
        width: 320px;
        height: 200px;
        background: #223;
        margin-bottom: 20px;
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
</style>
