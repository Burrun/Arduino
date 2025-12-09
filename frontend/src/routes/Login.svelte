<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let userId = "";
    let password = "";
    let isLoading = false;
    let errorMessage = "";

    async function handleLogin() {
        if (!userId.trim() || !password.trim()) {
            errorMessage = "아이디와 비밀번호를 입력해주세요.";
            return;
        }

        isLoading = true;
        errorMessage = "";

        try {
            await api.login(userId, password);
            console.log("[AUTH] Login successful for:", userId);
            
            // 로그인 정보 저장
            $authData.userId = userId;
            $authData.sessionId = userId;
            
            // 다음 단계로 (Standby)
            $currentStep = 1;
        } catch (error) {
            console.error("[AUTH] Login error:", error);
            if (error.response?.status === 400) {
                errorMessage = "아이디 또는 비밀번호가 잘못되었습니다.";
            } else {
                errorMessage = "서버 연결에 실패했습니다.";
            }
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="full-screen center column gap-20">
    <h1>AuthBox</h1>
    <p class="subtitle">로그인</p>

    <div class="login-form">
        <input
            type="text"
            class="input-field"
            placeholder="아이디"
            bind:value={userId}
            disabled={isLoading}
            on:keypress={(e) => e.key === 'Enter' && handleLogin()}
        />
        <input
            type="password"
            class="input-field"
            placeholder="비밀번호"
            bind:value={password}
            disabled={isLoading}
            on:keypress={(e) => e.key === 'Enter' && handleLogin()}
        />
        
        {#if errorMessage}
            <p class="error">{errorMessage}</p>
        {/if}
        
        <Button primary onClick={handleLogin} disabled={isLoading}>
            {isLoading ? "로그인 중..." : "로그인"}
        </Button>
    </div>
</div>

<style>
    .login-form {
        display: flex;
        flex-direction: column;
        gap: 15px;
        width: 100%;
        max-width: 320px;
    }
    .input-field {
        padding: 15px 20px;
        font-size: 1.1rem;
        background: #333;
        border: 2px solid #444;
        border-radius: 8px;
        color: #fff;
        text-align: center;
    }
    .input-field:focus {
        outline: none;
        border-color: #646cff;
    }
    .input-field:disabled {
        opacity: 0.6;
    }
    .error {
        color: #ff6b6b;
        font-size: 0.9rem;
        text-align: center;
        margin: 0;
    }
</style>
