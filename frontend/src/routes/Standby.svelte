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
            alert("인증 시작에 실패했습니다. 다시 시도해주세요.");
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
    <p class="subtitle">인증 준비</p>

    <div class="card">
        <p>사용자 ID: <strong>{$authData.userId || $authData.sessionId}</strong></p>
        <p>상태: {isLoading ? "연결 중..." : "준비 완료"}</p>
    </div>

    <div class="button-group">
        <Button onClick={logout} disabled={isLoading}>로그아웃</Button>
        <Button primary onClick={startVerification} disabled={isLoading}>
            {isLoading ? "시작 중..." : "인증 시작"}
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
