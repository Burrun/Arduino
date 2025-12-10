<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData, logId } from "../lib/store";

    let reporterName = "";
    let isLoading = false;

    async function submitOTP() {
        if (!reporterName.trim()) return;

        isLoading = true;

        try {
            const response = await fetch(`/api/verification/${$logId}/otp`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userReporter: reporterName.trim() }),
            });

            const data = await response.json();
            $authData.quizResult = data.isSuccess || false;
        } catch (error) {
            console.error("OTP Error:", error);
            $authData.quizResult = false;
        } finally {
            isLoading = false;
            $currentStep = 6; // Always go to next step
        }
    }
</script>

<div class="full-screen column">
    <StepIndicator current={3} />
    <h2 class="title">News OTP Verification</h2>

    <div class="content center column">
        <div class="prompt-box">
            <p class="prompt">
                Enter the name of a reporter who wrote one of the 5 most recent
                articles<br />
                in the society section of Donga Ilbo.
            </p>
            <p class="prompt-note">
                (If only external source articles exist, enter the source.)
            </p>
        </div>

        <div class="input-area">
            <input
                type="text"
                class="reporter-input"
                placeholder="Enter reporter name"
                bind:value={reporterName}
                disabled={isLoading}
                on:keypress={(e) => e.key === "Enter" && submitOTP()}
            />
        </div>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 4)} disabled={isLoading}
            >Back</Button
        >
        <Button
            primary
            disabled={!reporterName.trim() || isLoading}
            onClick={submitOTP}
        >
            {isLoading ? "Verifying..." : "Submit"}
        </Button>
    </div>
</div>

<style>
    .prompt-box {
        background: #2a2a3a;
        border: 1px solid #444;
        border-radius: 12px;
        padding: 25px 30px;
        margin-bottom: 25px;
        max-width: 600px;
        text-align: center;
    }
    .prompt {
        font-size: 1.2rem;
        line-height: 1.6;
        margin: 0;
        color: #e0e0e0;
    }
    .prompt-note {
        font-size: 1rem;
        color: #888;
        margin-top: 10px;
        margin-bottom: 0;
    }
    .input-area {
        width: 100%;
        max-width: 400px;
    }
    .reporter-input {
        width: 100%;
        padding: 15px 20px;
        font-size: 1.2rem;
        background: #333;
        border: 2px solid #444;
        border-radius: 8px;
        color: #fff;
        text-align: center;
    }
    .reporter-input:focus {
        outline: none;
        border-color: #646cff;
    }
    .reporter-input:disabled {
        opacity: 0.6;
    }
</style>
