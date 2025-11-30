<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData } from "../lib/store";

    function startSession() {
        $currentStep = 1; // Go to Checklist
    }
</script>

<div class="full-screen center column gap-20">
    <h1>AuthBox</h1>
    <p class="subtitle">Secure Multi-factor Authentication</p>

    <div class="card">
        <p>Session ID: <strong>{$authData.sessionId}</strong></p>
        <p>Status: Ready</p>
    </div>

    <Button primary onClick={startSession}>Start Authentication</Button>
</div>

<style>
    .card {
        background: #333;
        padding: 20px;
        border-radius: 8px;
        min-width: 300px;
    }
</style>
