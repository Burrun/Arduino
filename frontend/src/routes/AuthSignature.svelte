<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import SignaturePad from "../lib/SignaturePad.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle";
    let message = "Sign on the pad below";

    async function handleSave(event) {
        const imageData = event.detail;
        status = "capturing";
        message = "Recording signature...";
        try {
            const res = await api.captureSignature(imageData);
            $authData.signature = res.data.path;
            status = "success";
            message = "Signature recorded!";
        } catch (e) {
            status = "error";
            message = "Capture failed. Try again.";
        }
    }

    function next() {
        $currentStep = 7; // Go to Review
    }
</script>

<div class="full-screen column">
    <StepIndicator current={5} />
    <h2 class="title">Digital Signature</h2>

    <div class="content center column">
        {#if status !== "success"}
            <SignaturePad on:save={handleSave} />
        {:else}
            <div class="pad-box success">
                <span class="check">✓</span>
            </div>
        {/if}
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 5)}>Back</Button>
        {#if status === "success"}
            <Button primary onClick={next}>Next</Button>
        {/if}
    </div>
</div>

<style>
    .pad-box {
        width: 320px;
        height: 160px;
        background: #eee;
        color: #333;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px dashed #999;
        font-size: 3rem;
    }
    .pad-box.success {
        border-style: solid;
        border-color: #4caf50;
        background: #e8f5e9;
    }
</style>
