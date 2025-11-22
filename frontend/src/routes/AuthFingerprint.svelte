<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle"; // idle, scanning, success, error
    let message = "Place your finger on the sensor";

    async function scan() {
        status = "scanning";
        message = "Scanning...";
        try {
            const res = await api.captureFingerprint();
            $authData.fingerprint = res.data.path;
            status = "success";
            message = "Fingerprint captured!";
        } catch (e) {
            status = "error";
            message = "Scan failed. Try again.";
        }
    }

    function next() {
        $currentStep = 3; // Go to Camera
    }
</script>

<div class="full-screen column">
    <StepIndicator current={1} />
    <h2 class="title">Fingerprint Authentication</h2>

    <div class="content center column">
        <div
            class="icon-box"
            class:success={status === "success"}
            class:error={status === "error"}
        >
            <span class="icon">👆</span>
        </div>
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 1)}>Back</Button>
        {#if status !== "success"}
            <Button primary onClick={scan} disabled={status === "scanning"}>
                {status === "scanning" ? "Scanning..." : "Scan Fingerprint"}
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
