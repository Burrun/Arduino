<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";

    function next() {
        $currentStep = 9; // Go to EmailInput
    }
</script>

<div class="full-screen column">
    <StepIndicator current={6} />
    <h2 class="title">Review & Consent</h2>

    <div class="content">
        <div class="summary">
            <div class="row">
                <span>Fingerprint:</span>
                <span class="val"
                    >{$authData.fingerprint ? "Captured" : "Missing"}</span
                >
            </div>
            <div class="row">
                <span>Face Photo:</span>
                <span class="val"
                    >{$authData.camera ? "Captured" : "Missing"}</span
                >
            </div>
            <div class="row">
                <span>Quiz:</span>
                <span class="val"
                    >{$authData.quizResult ? "Passed" : "Failed"}</span
                >
            </div>
            <div class="row">
                <span>Location:</span>
                <span class="val">{$authData.gps ? "Verified" : "Missing"}</span
                >
            </div>
            <div class="row">
                <span>Signature:</span>
                <span class="val"
                    >{$authData.signature ? "Signed" : "Missing"}</span
                >
            </div>
        </div>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 7)}>Back</Button>
        <Button primary onClick={next}>Submit</Button>
    </div>
</div>

<style>
    .summary {
        background: #333;
        padding: 15px;
        border-radius: 8px;
        max-height: 300px;
        overflow-y: auto;
    }
    .row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #444;
    }
    .row:last-child {
        border-bottom: none;
    }
    .val {
        font-weight: bold;
        color: #aaa;
    }
</style>
