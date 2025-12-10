<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData } from "../lib/store";

    let senderEmail = "";
    let isLoading = false;
    let errorMessage = "";

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function handleSubmit() {
        if (!senderEmail.trim()) {
            errorMessage = "Please enter your email.";
            return;
        }
        if (!validateEmail(senderEmail)) {
            errorMessage = "Invalid email format.";
            return;
        }

        // 이메일 저장 후 다음 단계로
        $authData.senderEmail = senderEmail;
        $currentStep = 10; // Go to Sending
    }
</script>

<div class="full-screen center column gap-20">
    <h2 class="title">Result Email</h2>
    <p class="subtitle">
        Enter the email address to receive the verification result.
    </p>

    <div class="email-form">
        <input
            type="email"
            class="input-field"
            placeholder="example@email.com"
            bind:value={senderEmail}
            disabled={isLoading}
            on:keypress={(e) => e.key === "Enter" && handleSubmit()}
        />

        {#if errorMessage}
            <p class="error">{errorMessage}</p>
        {/if}
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 8)}>Back</Button>
        <Button
            primary
            onClick={handleSubmit}
            disabled={isLoading || !senderEmail.trim()}
        >
            Send
        </Button>
    </div>
</div>

<style>
    .subtitle {
        color: #888;
        margin-bottom: 10px;
    }
    .email-form {
        display: flex;
        flex-direction: column;
        gap: 10px;
        width: 100%;
        max-width: 400px;
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
    .error {
        color: #ff6b6b;
        font-size: 0.9rem;
        text-align: center;
        margin: 0;
    }
    .footer {
        display: flex;
        gap: 15px;
        margin-top: 20px;
    }
</style>
