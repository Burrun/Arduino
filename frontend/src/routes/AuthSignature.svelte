<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import SignaturePad from "../lib/SignaturePad.svelte";
    import { currentStep, authData, logId } from "../lib/store";
    import { api } from "../lib/api";
    import { get } from "svelte/store";

    // Two-step flow: consent -> signature
    let step = "consent"; // "consent" or "signature"
    let agreed = false;

    let status = "idle";
    let message = "서명란에 서명해주세요";
    let signaturePad;

    function proceedToSignature() {
        if (agreed) {
            step = "signature";
        }
    }

    async function handleSave(event) {
        const imageData = event.detail;
        status = "capturing";
        message = "서명 저장 중...";

        // Debugging: Check logId
        const currentLogId = get(logId);
        console.log("Current Log ID:", currentLogId);

        try {
            if (!currentLogId) {
                // For UI testing without real session
                console.warn("No logId found. Running in UI Test Mode.");
                // Simulate API delay
                await new Promise((r) => setTimeout(r, 1000));
                $authData.signature = imageData; // Just save locally to store
                status = "success";
                message = "서명이 저장되었습니다! (테스트 모드)";
                return;
            }

            // Use AuthBox verification API
            const res = await api.verifySignature(imageData);
            $authData.signature = res.data.filePath || res.data.path;
            status = "success";
            message = "서명이 저장되었습니다!";
        } catch (e) {
            console.error("Signature error:", e);
            status = "error";
            message =
                e.response?.data?.detail || "저장 실패. 다시 시도해주세요.";
        }
    }

    function handleClear() {
        if (signaturePad) {
            signaturePad.clear();
        }
    }

    function handleSaveClick() {
        if (signaturePad) {
            signaturePad.save();
        }
    }

    function next() {
        $currentStep = 8; // Go to Review
    }
</script>

<div class="full-screen column">
    <StepIndicator current={6} />

    {#if step === "consent"}
        <!-- Step 1: Consent -->
        <h2 class="title">본인 확인 및 처벌 고지</h2>

        <div class="content center column">
            <div class="pledge-wrapper">
                <img
                    src="/pledge.png"
                    alt="본인 확인 및 처벌 고지"
                    class="pledge-image"
                />
                <label class="checkbox-overlay">
                    <input
                        type="checkbox"
                        bind:checked={agreed}
                        class="checkbox-input"
                    />
                    {#if agreed}
                        <div class="checkbox-check">✔</div>
                    {/if}
                </label>
            </div>
        </div>

        <div class="footer">
            <Button onClick={() => ($currentStep = 6)}>Back</Button>
            <Button primary disabled={!agreed} onClick={proceedToSignature}>
                서명하기
            </Button>
        </div>
    {:else}
        <!-- Step 2: Signature -->
        <h2 class="title">전자 서명</h2>

        <div class="content center column">
            {#if status !== "success"}
                <SignaturePad
                    bind:this={signaturePad}
                    width={500}
                    height={240}
                    on:save={handleSave}
                />
            {:else}
                <div class="pad-box success">
                    <span class="check">✓</span>
                </div>
            {/if}
            <p class="status-text">{message}</p>
        </div>

        <div class="footer">
            <Button onClick={() => (step = "consent")}>Back</Button>
            <div class="sig-buttons">
                {#if status !== "success"}
                    <Button onClick={handleClear}>지우기</Button>
                    <Button onClick={handleSaveClick}>서명 저장</Button>
                {/if}
            </div>
            {#if status === "success"}
                <Button primary onClick={next}>다음</Button>
            {/if}
        </div>
    {/if}
</div>

<style>
    .pledge-wrapper {
        position: relative;
        display: inline-block;
        margin-top: 50px;
    }
    .pledge-image {
        display: block;
        max-width: 550px;
        width: 100%;
        height: auto;
        border-radius: 8px;
    }
    .checkbox-overlay {
        position: absolute;
        /* Position over the checkbox in the image */
        left: 10%;
        bottom: 33%;
        width: 35px;
        height: 35px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .checkbox-overlay .checkbox-input {
        width: 100%;
        height: 100%;
        cursor: pointer;
        accent-color: #000;
        margin: 0;
        opacity: 0; /* Hide default checkbox but keep it clickable */
    }
    /* Custom checkmark when agreed */
    .checkbox-check {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        font-size: 2.5rem;
        font-weight: bold;
        line-height: 1;
        padding-bottom: 5px; /* Fine tuning vertical align for the character */
    }
    .pad-box {
        width: 500px;
        height: 240px;
        background: #eee;
        color: #333;
        margin-bottom: 10px;
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
    .status-text {
        margin-top: 5px;
    }
    .sig-buttons {
        display: flex;
        gap: 10px;
    }
</style>
