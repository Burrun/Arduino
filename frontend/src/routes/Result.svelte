<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData, resetAuthData } from "../lib/store";

    function restart() {
        resetAuthData();
        $currentStep = 0;
    }
</script>

<div class="full-screen center column">
    <div class="icon">✅</div>
    <h1>Authentication Successful</h1>
    <p class="subtitle">
        Verification completed for user: <strong
            >{$authData.userId || "Unknown"}</strong
        >
    </p>

    {#if $authData.logId}
        <p class="session-info">Session ID: {$authData.logId}</p>
    {/if}

    <div class="summary">
        <div class="row">
            <span>Fingerprint</span>
            <span class="status ok">{$authData.fingerprint ? "✓" : "–"}</span>
        </div>
        <div class="row">
            <span>Face Recognition</span>
            <span class="status ok">{$authData.camera ? "✓" : "–"}</span>
        </div>
        <div class="row">
            <span>OTP Quiz</span>
            <span
                class="status"
                class:ok={$authData.otpResult}
                class:fail={!$authData.otpResult}
            >
                {$authData.otpResult ? "✓" : "✗"}
            </span>
        </div>
        <div class="row">
            <span>GPS Location</span>
            <span class="status ok">{$authData.gps ? "✓" : "–"}</span>
        </div>
        <div class="row">
            <span>Signature</span>
            <span class="status ok">{$authData.signature ? "✓" : "–"}</span>
        </div>
    </div>

    <div class="spacer"></div>

    <Button primary onClick={restart}>Done</Button>
</div>

<style>
    .icon {
        font-size: 5rem;
        margin-bottom: 20px;
    }
    .subtitle {
        color: #aaa;
        margin-bottom: 10px;
    }
    .session-info {
        font-family: monospace;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    .summary {
        background: #333;
        padding: 15px 20px;
        border-radius: 8px;
        min-width: 280px;
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
    .status {
        font-weight: bold;
    }
    .status.ok {
        color: #4caf50;
    }
    .status.fail {
        color: #ff6b6b;
    }
    .spacer {
        height: 30px;
    }
</style>
