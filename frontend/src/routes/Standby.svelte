<script>
    import Button from "../lib/Button.svelte";
    import { currentStep, authData } from "../lib/store";
    import { api } from "../lib/api";

    let userId = "";
    let status = "idle"; // idle, loading, error
    let errorMessage = "";

    async function startSession() {
        if (!userId.trim()) {
            errorMessage = "Please enter your User ID";
            return;
        }

        status = "loading";
        errorMessage = "";

        try {
            const res = await api.startVerification(userId);
            $authData.logId = res.data.logId;
            $authData.userId = userId;
            console.log(
                "[START] Verification started with logId:",
                res.data.logId,
            );
            $currentStep = 1; // Go to Checklist
        } catch (e) {
            status = "error";
            errorMessage =
                e.response?.data?.detail || "Failed to start verification";
            console.error("[START] Error:", e);
        }
    }
</script>

<div class="full-screen center column gap-20">
    <h1>AuthBox</h1>
    <p class="subtitle">Secure Multi-factor Authentication</p>

    <div class="card">
        <label for="userId">User ID</label>
        <input
            id="userId"
            type="text"
            bind:value={userId}
            placeholder="Enter your ID"
            disabled={status === "loading"}
            on:keypress={(e) => e.key === "Enter" && startSession()}
        />
        {#if errorMessage}
            <p class="error">{errorMessage}</p>
        {/if}
    </div>

    <Button primary onClick={startSession} disabled={status === "loading"}>
        {status === "loading" ? "Starting..." : "Start Authentication"}
    </Button>
</div>

<style>
    .card {
        background: #333;
        padding: 20px;
        border-radius: 8px;
        min-width: 300px;
    }
    label {
        display: block;
        margin-bottom: 8px;
        font-weight: bold;
        color: #aaa;
    }
    input {
        width: 100%;
        padding: 12px;
        font-size: 1rem;
        border: 2px solid #555;
        border-radius: 6px;
        background: #222;
        color: #fff;
        box-sizing: border-box;
    }
    input:focus {
        outline: none;
        border-color: #646cff;
    }
    input:disabled {
        opacity: 0.6;
    }
    .error {
        color: #ff6b6b;
        margin-top: 10px;
        font-size: 0.9rem;
    }
</style>
