<script>
    import Button from "../lib/Button.svelte";
    import StepIndicator from "../lib/StepIndicator.svelte";
    import { currentStep, authData } from "../lib/store";

    let selected = null;
    const answer = "B"; // Mock answer

    function select(option) {
        selected = option;
    }

    function next() {
        $authData.quizResult = selected === answer;
        $currentStep = 5; // Go to GPS
    }
</script>

<div class="full-screen column">
    <StepIndicator current={3} />
    <h2 class="title">Security Quiz</h2>

    <div class="content center column">
        <p class="question">What is the capital of South Korea?</p>

        <div class="options">
            <button
                class="option"
                class:selected={selected === "A"}
                on:click={() => select("A")}
            >
                A. Busan
            </button>
            <button
                class="option"
                class:selected={selected === "B"}
                on:click={() => select("B")}
            >
                B. Seoul
            </button>
            <button
                class="option"
                class:selected={selected === "C"}
                on:click={() => select("C")}
            >
                C. Incheon
            </button>
        </div>
    </div>

    <div class="footer">
        <Button onClick={() => ($currentStep = 3)}>Back</Button>
        <Button primary disabled={!selected} onClick={next}>Next</Button>
    </div>
</div>

<style>
    .question {
        font-size: 1.4rem;
        margin-bottom: 15px;
    }
    .options {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        width: 100%;
        max-width: 650px;
    }
    .option {
        padding: 15px 10px;
        background: #333;
        border: 2px solid #444;
        border-radius: 8px;
        text-align: center;
        font-size: 1.1rem;
    }
    .option.selected {
        border-color: #646cff;
        background: #2e2e3f;
    }
</style>
