<script>
    export let onClick = () => {};
    export let disabled = false;
    export let primary = false;
    export let danger = false;
</script>

<button class:primary class:danger on:click={onClick} {disabled}>
    <slot />
</button>

<style>
    button {
        padding: 15px 30px;
        font-size: 1.2rem;
        border-radius: 8px;
        border: none;
        background-color: #333;
        color: white;
        cursor: pointer;
        transition: all 0.2s;
        min-width: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }

    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    button:active:not(:disabled) {
        transform: scale(0.98);
    }

    .primary {
        background-color: #646cff;
    }
    .primary:hover:not(:disabled) {
        background-color: #747bff;
    }

    .danger {
        background-color: #ff4444;
    }
    .danger:hover:not(:disabled) {
        background-color: #ff6666;
    }
</style>
