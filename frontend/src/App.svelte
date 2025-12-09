<script>
  import Header from "./lib/Header.svelte";
  import { currentStep } from "./lib/store";

  import Login from "./routes/Login.svelte";
  import Standby from "./routes/Standby.svelte";
  import Checklist from "./routes/Checklist.svelte";
  import AuthFingerprint from "./routes/AuthFingerprint.svelte";
  import AuthCamera from "./routes/AuthCamera.svelte";
  import AuthQuiz from "./routes/AuthQuiz.svelte";
  import AuthGPS from "./routes/AuthGPS.svelte";
  import AuthSignature from "./routes/AuthSignature.svelte";
  import Review from "./routes/Review.svelte";
  import EmailInput from "./routes/EmailInput.svelte";
  import Sending from "./routes/Sending.svelte";
  import Result from "./routes/Result.svelte";
</script>

<Header />

<main>
  {#if $currentStep === 0}
    <Login />
  {:else if $currentStep === 1}
    <Standby />
  {:else if $currentStep === 2}
    <Checklist />
  {:else if $currentStep === 3}
    <AuthFingerprint />
  {:else if $currentStep === 4}
    <AuthCamera />
  {:else if $currentStep === 5}
    <AuthQuiz />
  {:else if $currentStep === 6}
    <AuthGPS />
  {:else if $currentStep === 7}
    <AuthSignature />
  {:else if $currentStep === 8}
    <Review />
  {:else if $currentStep === 9}
    <EmailInput />
  {:else if $currentStep === 10}
    <Sending />
  {:else if $currentStep === 11}
    <Result />
  {/if}
</main>

<style>
  main {
    flex: 1;
    overflow: hidden;
  }

  .skip-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 10px 20px;
    background-color: #ff4444;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    z-index: 9999;
    font-weight: bold;
    opacity: 0.7;
    transition: opacity 0.2s;
  }

  .skip-btn:hover {
    opacity: 1;
  }
</style>

<button class="skip-btn" on:click={() => $currentStep++}>
  SKIP (Test)
</button>
