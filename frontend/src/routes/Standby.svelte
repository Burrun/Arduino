<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData, logId } from "../lib/store";
    import { api } from "../lib/api";

    let isLoading = false;

    async function startVerification() {
        isLoading = true;
        try {
            // 인증 시작 (logId 발급)
            const res = await api.startVerification($authData.userId);
            const receivedLogId = res.data.logId;
            $logId = receivedLogId;
            console.log("[AUTH] Verification started, logId:", receivedLogId);

            // 다음 단계로 (Checklist)
            $currentStep = 2;
        } catch (error) {
            console.error("[AUTH] Start verification error:", error);
            alert("Failed to start verification. Please try again.");
        } finally {
            isLoading = false;
        }
    }

    function logout() {
        $authData.userId = null;
        $logId = null;
        $currentStep = 0; // Back to login
    }
</script>

<div class="full-screen center column gap-20">
    <h1>AuthBox</h1>
    <p class="subtitle">Verification Ready</p>

    <div class="card">
        <p>
            User ID: <strong>{$authData.userId || $authData.sessionId}</strong>
        </p>
        <p>Status: {isLoading ? "Connecting..." : "Ready"}</p>
    </div>

    <div class="button-group">
        <Button onClick={logout} disabled={isLoading}>Logout</Button>
        <Button primary onClick={startVerification} disabled={isLoading}>
            {isLoading ? "Starting..." : "Start Verification"}
        </Button>
    </div>
</div>

<style>
    .card {
        background: #333;
        padding: 20px;
        border-radius: 8px;
        min-width: 300px;
    }
    .button-group {
        display: flex;
        gap: 15px;
    }
</style>
