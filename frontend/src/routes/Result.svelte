<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData, logs } from "../lib/store";

    function restart() {
        $authData = {
            sessionId: "SESSION-" + Math.floor(Math.random() * 1000),
            timestamp: "",
            fingerprint: null,
            camera: null,
            gps: null,
            signature: null,
            quizResult: null,
        };
        $logs = [];
        $currentStep = 0;
    }
</script>

<div class="full-screen center column">
    <div class="icon">✅</div>
    <h1>Authentication Successful</h1>
    <p class="subtitle">Transfer authorized.</p>

    <div class="spacer"></div>

    <Button primary onClick={restart}>Done</Button>
</div>

<style>
    .icon {
        font-size: 5rem;
        margin-bottom: 20px;
    }
    .spacer {
        height: 40px;
    }
</style>
