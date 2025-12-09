<script>
    import { onMount } from "svelte";
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData, otpData } from "../lib/store";
    import { api } from "../lib/api";

    let status = "loading"; // loading, ready, submitting, success, error
    let message = "Loading quiz...";
    let selected = null;

    onMount(async () => {
        await loadOTPQuestion();
    });

    async function loadOTPQuestion() {
        status = "loading";
        message = "Loading quiz...";

        try {
            const res = await api.getOTP();
            $otpData = {
                question: res.data.question,
                options: res.data.options || [],
                newsTitle: res.data.newsTitle || "",
                selectedAnswer: null,
            };
            status = "ready";
            message = "";
        } catch (e) {
            status = "error";
            message = "Failed to load quiz. Using fallback question.";
            // Fallback for local mode
            $otpData = {
                question: "What is the capital of South Korea?",
                options: ["A. Busan", "B. Seoul", "C. Incheon", "D. Daegu"],
                newsTitle: "(Offline Mode)",
                selectedAnswer: null,
            };
            status = "ready";
        }
    }

    function selectOption(option) {
        selected = option;
        $otpData.selectedAnswer = option;
    }

    async function submitAnswer() {
        if (!selected) return;

        status = "submitting";
        message = "Checking answer...";

        try {
            const res = await api.submitOTP(selected);
            $authData.otpResult = res.data.isCorrect;
            status = "success";
            message = res.data.isCorrect
                ? "Correct!"
                : "Incorrect, but continuing...";

            // Auto-advance after 1.5 seconds
            setTimeout(() => {
                $currentStep = 5; // Go to GPS
            }, 1500);
        } catch (e) {
            status = "error";
            message = "Verification failed. Please try again.";
        }
    }

    function extractOptionLetter(option) {
        // Extract "A", "B", "C", etc. from options like "A. Seoul"
        const match = option.match(/^([A-Z])\./);
        return match ? match[1] : option;
    }
</script>

<div class="full-screen column">
    <StepIndicator current={3} />
    <h2 class="title">Security Quiz (OTP)</h2>

    <div class="content center column">
        {#if $otpData.newsTitle}
            <p class="news-hint">{$otpData.newsTitle}</p>
        {/if}

        <p class="question">{$otpData.question}</p>

        <div class="options">
            {#each $otpData.options as option}
                <button
                    class="option"
                    class:selected={selected === extractOptionLetter(option)}
                    on:click={() => selectOption(extractOptionLetter(option))}
                    disabled={status === "submitting" || status === "success"}
                >
                    {option}
                </button>
            {/each}
        </div>

        {#if message}
            <p
                class="status-text"
                class:success={status === "success"}
                class:error={status === "error"}
            >
                {message}
            </p>
        {/if}
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 3)}>Back</Button>
        {#if status !== "success"}
            <Button
                primary
                disabled={!selected ||
                    status === "submitting" ||
                    status === "loading"}
                onClick={submitAnswer}
            >
                {status === "submitting" ? "Checking..." : "Submit Answer"}
            </Button>
        {/if}
    </div>
</div>

<style>
    .news-hint {
        font-size: 0.9rem;
        color: #888;
        margin-bottom: 10px;
        font-style: italic;
    }
    .question {
        font-size: 1.4rem;
        margin-bottom: 15px;
        text-align: center;
    }
    .options {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        width: 100%;
        max-width: 500px;
    }
    .option {
        padding: 15px 10px;
        background: #333;
        border: 2px solid #444;
        border-radius: 8px;
        text-align: center;
        font-size: 1.1rem;
        color: white;
        cursor: pointer;
        transition: all 0.2s;
    }
    .option:hover:not(:disabled) {
        border-color: #555;
        background: #3a3a3a;
    }
    .option.selected {
        border-color: #646cff;
        background: #2e2e3f;
    }
    .option:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
    .status-text {
        margin-top: 15px;
        font-size: 1rem;
    }
    .status-text.success {
        color: #4caf50;
    }
    .status-text.error {
        color: #ff6b6b;
    }
</style>
