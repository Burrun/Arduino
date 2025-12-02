<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let status = "idle";
    let message = "Look at the camera";
    let imagePath = null;

    async function capture() {
        status = "capturing";
        message = "Capturing...";
        try {
            const res = await api.captureCamera();
            $authData.camera = res.data.path;
            imagePath = res.data.path;
            status = "success";
            message = "Photo captured!";
        } catch (e) {
            status = "error";
            message = "Capture failed. Try again.";
        }
    }

    function next() {
        $currentStep = 4; // Go to Quiz
    }
</script>

<div class="full-screen column">
    <StepIndicator current={2} />
    <h2 class="title">Face Authentication</h2>

    <div class="content center column">
        <div class="camera-box">
            {#if status === "success"}
                <div class="placeholder">Photo Captured</div>
            {:else}
                <div class="placeholder">Camera Preview</div>
            {/if}
        </div>
        <p class="status-text">{message}</p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 2)}>Back</Button>
        {#if status !== "success"}
            <Button primary onClick={capture} disabled={status === "capturing"}>
                {status === "capturing" ? "Capturing..." : "Take Photo"}
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
        border: 2px solid #555;
    }
    .placeholder {
        color: #666;
    }
    .status-text {
        margin-top: 5px;
    }
</style>
