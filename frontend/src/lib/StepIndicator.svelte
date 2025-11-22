<script>
    export let current = 1;
    export let total = 6;
</script>

<div class="steps">
    {#each Array(total) as _, i}
        <div class="step" class:active={i + 1 <= current}>
            {i + 1}
        </div>
        {#if i < total - 1}
            <div class="line" class:active={i + 1 < current}></div>
        {/if}
    {/each}
</div>

<style>
    .steps {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
    }
    .step {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #333;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #888;
        border: 2px solid #444;
    }
    .step.active {
        background-color: #646cff;
        color: white;
        border-color: #646cff;
    }
    .line {
        width: 30px;
        height: 2px;
        background-color: #333;
    }
    .line.active {
        background-color: #646cff;
    }
</style>
