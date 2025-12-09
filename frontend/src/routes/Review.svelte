<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";

    let email = "";

    function next() {
        $authData.email = email;
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
                <span>OTP Quiz:</span>
                <span
                    class="val"
                    class:success={$authData.otpResult}
                    class:fail={$authData.otpResult === false}
                >
                    {$authData.otpResult === null
                        ? "Not taken"
                        : $authData.otpResult
                          ? "Passed"
                          : "Failed"}
                </span>
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

        <div class="email-section">
            <label for="email">Email for result notification (optional)</label>
            <input
                id="email"
                type="email"
                bind:value={email}
                placeholder="your@email.com"
            />
        </div>

        <p class="consent-text">
            By clicking Submit, you consent to the processing of your biometric
            data for verification purposes.
        </p>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 6)}>Back</Button>
        <Button primary onClick={next}>Submit</Button>
    </div>
</div>

<style>
    .summary {
        background: #333;
        padding: 15px;
        border-radius: 8px;
        max-height: 200px;
        overflow-y: auto;
        margin-bottom: 20px;
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
    .val.success {
        color: #4caf50;
    }
    .val.fail {
        color: #ff6b6b;
    }
    .email-section {
        margin-bottom: 20px;
    }
    .email-section label {
        display: block;
        margin-bottom: 8px;
        color: #888;
        font-size: 0.9rem;
    }
    .email-section input {
        width: 100%;
        padding: 12px;
        font-size: 1rem;
        border: 2px solid #555;
        border-radius: 6px;
        background: #222;
        color: #fff;
        box-sizing: border-box;
    }
    .email-section input:focus {
        outline: none;
        border-color: #646cff;
    }
    .consent-text {
        font-size: 0.85rem;
        color: #666;
        text-align: center;
        line-height: 1.5;
    }
</style>
