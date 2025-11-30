<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";

    let agreed = false;

    function next() {
        $currentStep = 8; // Go to Sending
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

        <div class="consent">
            <label>
                <input type="checkbox" bind:checked={agreed} />
                I agree to the collection and use of my biometric and location data
                for authentication purposes.
            </label>
        </div>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 6)}>Back</Button>
        <Button primary disabled={!agreed} onClick={next}>Submit</Button>
    </div>
</div>

<style>
    .summary {
        background: #333;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #444;
    }
    .row:last-child {
        border-bottom: none;
    }
    .val {
        font-weight: bold;
        color: #aaa;
    }
    .consent {
        font-size: 1.1rem;
        padding: 10px;
    }
    input[type="checkbox"] {
        transform: scale(1.5);
        margin-right: 10px;
    }
</style>
