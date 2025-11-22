<script>
  import Header from "./lib/Header.svelte";
  import { currentStep } from "./lib/store";

  import Standby from "./routes/Standby.svelte";
  import Checklist from "./routes/Checklist.svelte";
  import AuthFingerprint from "./routes/AuthFingerprint.svelte";
  import AuthCamera from "./routes/AuthCamera.svelte";
  import AuthQuiz from "./routes/AuthQuiz.svelte";
  import AuthGPS from "./routes/AuthGPS.svelte";
  import AuthSignature from "./routes/AuthSignature.svelte";
  import Review from "./routes/Review.svelte";
  import Sending from "./routes/Sending.svelte";
  import Result from "./routes/Result.svelte";
</script>

<Header />

<main>
  {#if $currentStep === 0}
    <Standby />
  {:else if $currentStep === 1}
    <Checklist />
  {:else if $currentStep === 2}
    <AuthFingerprint />
  {:else if $currentStep === 3}
    <AuthCamera />
  {:else if $currentStep === 4}
    <AuthQuiz />
  {:else if $currentStep === 5}
    <AuthGPS />
  {:else if $currentStep === 6}
    <AuthSignature />
  {:else if $currentStep === 7}
    <Review />
  {:else if $currentStep === 8}
    <Sending />
  {:else if $currentStep === 9}
    <Result />
  {/if}
</main>

<style>
  main {
    flex: 1;
    overflow: hidden;
  }
</style>
