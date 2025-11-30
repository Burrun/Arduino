<script>
  import { onMount, createEventDispatcher } from "svelte";

  export let width = 300;
  export let height = 150;

  let canvas;
  let ctx;
  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;

  const dispatch = createEventDispatcher();

  onMount(() => {
    ctx = canvas.getContext("2d");
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeStyle = "#000";
  });

  function getCoords(e) {
    const rect = canvas.getBoundingClientRect();
    let clientX, clientY;

    if (e.touches && e.touches.length > 0) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }

    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  }

  function startDrawing(e) {
    isDrawing = true;
    const { x, y } = getCoords(e);
    lastX = x;
    lastY = y;
  }

  function draw(e) {
    if (!isDrawing) return;
    e.preventDefault(); // Prevent scrolling on touch

    const { x, y } = getCoords(e);

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();

    lastX = x;
    lastY = y;
  }

  function stopDrawing() {
    isDrawing = false;
  }

  function clear() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  function save() {
    const dataURL = canvas.toDataURL("image/png");
    dispatch("save", dataURL);
  }
</script>

<div class="signature-pad">
  <canvas
    bind:this={canvas}
    {width}
    {height}
    on:mousedown={startDrawing}
    on:mousemove={draw}
    on:mouseup={stopDrawing}
    on:mouseout={stopDrawing}
    on:touchstart={startDrawing}
    on:touchmove={draw}
    on:touchend={stopDrawing}
    on:blur={stopDrawing}
  ></canvas>
  <div class="buttons">
    <button on:click={clear}>Clear</button>
    <button on:click={save} class="primary">Save Signature</button>
  </div>
</div>

<style>
  .signature-pad {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }

  canvas {
    border: 1px solid #ccc;
    background: #fff;
    cursor: crosshair;
    touch-action: none; /* Important for touch devices */
  }

  .buttons {
    display: flex;
    gap: 10px;
  }

  button {
    padding: 8px 16px;
    border: 1px solid #ccc;
    background: #f0f0f0;
    cursor: pointer;
    border-radius: 4px;
  }

  button.primary {
    background: #007bff;
    color: white;
    border-color: #0056b3;
  }
</style>
