<script>
  import { onMount } from 'svelte';
  import { authData } from './store';

  let time = new Date().toLocaleTimeString();
  let battery = 100;
  let wifi = true;

  onMount(() => {
    const interval = setInterval(() => {
      time = new Date().toLocaleTimeString();
    }, 1000);
    return () => clearInterval(interval);
  });
</script>

<header class="status-bar">
  <div class="left">
    <span>Session: {$authData.sessionId}</span>
  </div>
  <div class="right">
    <span>{wifi ? 'WiFi Connected' : 'No WiFi'}</span>
    <span class="separator">|</span>
    <span>Bat: {battery}%</span>
    <span class="separator">|</span>
    <span>{time}</span>
  </div>
</header>

<style>
  .status-bar {
    background-color: #222;
    color: #fff;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 15px;
    font-size: 0.8rem;
    border-bottom: 1px solid #444;
  }
  .separator {
    margin: 0 8px;
    color: #666;
  }
  .right {
    display: flex;
    align-items: center;
  }
</style>
