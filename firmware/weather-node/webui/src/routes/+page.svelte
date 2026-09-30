<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Activity,
    Battery,
    Compass,
    Cpu,
    Droplets,
    Gauge,
    Power,
    RefreshCw,
    Search,
    Thermometer,
    Wind,
    Wifi
  } from 'lucide-svelte';

  interface Telemetry {
    node_id: number;
    uptime_s: number;
    battery_v: number;
    battery_raw_mv: number;
    bme_temp: number;
    bme_hum: number;
    bme_press: number;
    ds18b20_temp: number;
    wind_speed: number;
    wind_dir: number;
    rain_tips: number;
    rain_mm: number;
    soil_moist: number;
    soil_raw_mv: number;
    mosfet_on: boolean;
    ap_ip: string;
    sta_ip: string;
    mdns: string;
  }

  let data = $state<Telemetry | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let autoRefresh = $state(true);
  let togglingMosfet = $state(false);
  let scanningI2c = $state(false);
  let i2cDevices = $state<string[] | null>(null);
  let resettingRain = $state(false);

  // WiFi Settings Form
  let showWifiSettings = $state(false);
  let wifiSsid = $state('');
  let wifiPass = $state('');
  let wifiSaved = $state(false);

  async function fetchTelemetry() {
    try {
      const res = await fetch('/api/telemetry');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      error = null;
    } catch (err: any) {
      error = err.message || 'Connection lost';
    } finally {
      loading = false;
    }
  }

  async function toggleMosfet() {
    togglingMosfet = true;
    try {
      const res = await fetch('/api/mosfet', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        if (data) data.mosfet_on = json.mosfet_on;
      }
    } catch (e) {
      console.error(e);
    } finally {
      togglingMosfet = false;
    }
  }

  async function scanI2c() {
    scanningI2c = true;
    i2cDevices = null;
    try {
      const res = await fetch('/api/scan-i2c');
      if (res.ok) {
        const json = await res.json();
        i2cDevices = json.devices || [];
      }
    } catch (e) {
      console.error(e);
    } finally {
      scanningI2c = false;
    }
  }

  async function resetRain() {
    resettingRain = true;
    try {
      const res = await fetch('/api/rain/reset', { method: 'POST' });
      if (res.ok) {
        if (data) {
          data.rain_tips = 0;
          data.rain_mm = 0.0;
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      resettingRain = false;
    }
  }

  async function saveWifi() {
    if (!wifiSsid) return;
    try {
      const res = await fetch('/api/wifi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ssid: wifiSsid, password: wifiPass })
      });
      if (res.ok) {
        wifiSaved = true;
        setTimeout(() => (wifiSaved = false), 4000);
      }
    } catch (e) {
      console.error(e);
    }
  }

  function getWindDirectionCardinal(deg: number): string {
    if (deg >= 337.5 || deg < 22.5) return 'N';
    if (deg >= 22.5 && deg < 67.5) return 'NE';
    if (deg >= 67.5 && deg < 112.5) return 'E';
    if (deg >= 112.5 && deg < 157.5) return 'SE';
    if (deg >= 157.5 && deg < 202.5) return 'S';
    if (deg >= 202.5 && deg < 247.5) return 'SW';
    if (deg >= 247.5 && deg < 292.5) return 'W';
    return 'NW';
  }

  // 4S LiFePO4 state of charge, derived from rested pack voltage.
  // LiFePO4 has a very flat discharge curve, so a linear map is badly wrong:
  // at 12.64 V this pack is ~15% full, not 100%.
  // Each point is [pack volts, percent]; per-cell rest voltage x 4.
  // Values between points are linearly interpolated.
  const LIFEPO4_4S: number[][] = [
    [10.00, 0], [12.00, 5], [12.40, 10], [12.80, 20], [12.88, 30],
    [13.00, 40], [13.04, 50], [13.08, 60], [13.20, 70], [13.28, 80],
    [13.40, 90], [13.60, 99], [13.80, 100]
  ];

  function getBatteryPercent(v: number): number {
    if (!Number.isFinite(v) || v <= LIFEPO4_4S[0][0]) return 0;
    const last = LIFEPO4_4S[LIFEPO4_4S.length - 1];
    if (v >= last[0]) return 100;

    for (let i = 1; i < LIFEPO4_4S.length; i++) {
      const [v0, p0] = LIFEPO4_4S[i - 1];
      const [v1, p1] = LIFEPO4_4S[i];
      if (v <= v1) return Math.round(p0 + ((v - v0) / (v1 - v0)) * (p1 - p0));
    }
    return 100;
  }

  onMount(() => {
    fetchTelemetry();
    const interval = setInterval(() => {
      if (autoRefresh) fetchTelemetry();
    }, 1500);
    return () => clearInterval(interval);
  });
</script>

<div class="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
  <!-- Top Bar -->
  <header class="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl backdrop-blur-md">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="relative flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-bold">
          <Activity class="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="font-bold text-lg text-slate-100">Weather Node #{data?.node_id ?? 1}</h1>
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium {error ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}">
              <span class="w-1.5 h-1.5 rounded-full {error ? 'bg-red-500' : 'bg-emerald-500'}"></span>
              {error ? 'Offline' : 'Live'}
            </span>
          </div>
          <p class="text-xs text-slate-400">
            mDNS: <a href="http://weather.local" class="text-cyan-400 underline font-mono">http://weather.local</a>
            <span class="mx-1 text-slate-600">·</span>
            IP: <span class="font-mono text-slate-300">{data?.sta_ip || data?.ap_ip || '192.168.4.1'}</span>
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          onclick={() => fetchTelemetry()}
          class="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          title="Manual Refresh"
        >
          <RefreshCw class="w-4 h-4 {loading ? 'animate-spin' : ''}" />
        </button>
      </div>
    </div>
  </header>

  {#if error}
    <div class="bg-red-950/40 border border-red-800/60 text-red-300 p-3.5 rounded-xl text-xs flex items-center justify-between">
      <span>{error} — ESP32 not responding or disconnected from WiFi</span>
      <button onclick={fetchTelemetry} class="underline font-semibold ml-2">Retry</button>
    </div>
  {/if}

  <!-- Battery & Power Status -->
  <section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-slate-300 font-semibold text-sm">
        <Battery class="w-4 h-4 text-emerald-400" />
        <span>12V Battery Power Rail</span>
      </div>
      <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
        ADC: {data?.battery_raw_mv ?? '—'} mV
      </span>
    </div>

    <div class="flex items-end justify-between">
      <div>
        <div class="text-2xl font-black text-slate-100 font-mono tracking-tight">
          {data ? data.battery_v.toFixed(2) : '—'} <span class="text-sm font-normal text-slate-400">V</span>
        </div>
        <p class="text-xs text-slate-400">
          4S LiFePO4 · <span class="font-mono">{data ? (data.battery_v / 4).toFixed(2) : '—'}</span> V/cell
        </p>
      </div>
      <div class="text-right">
        <span class="text-sm font-bold font-mono {data && getBatteryPercent(data.battery_v) > 20 ? 'text-emerald-400' : 'text-amber-400'}">
          {data ? getBatteryPercent(data.battery_v) : 0}%
        </span>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
      <div
        class="h-full bg-emerald-500 transition-all duration-500"
        style="width: {data ? getBatteryPercent(data.battery_v) : 0}%"
      ></div>
    </div>
  </section>

  <!-- Sensor Grid -->
  <div class="grid grid-cols-2 gap-3">
    <!-- Temperature -->
    <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between">
      <div class="flex items-center justify-between text-slate-400 text-xs">
        <span>Temperature</span>
        <Thermometer class="w-4 h-4 text-orange-400" />
      </div>
      <div class="my-2">
        <div class="text-2xl font-black text-slate-100 font-mono">
          {data ? data.bme_temp.toFixed(1) : '—'} <span class="text-sm font-normal text-slate-400">°C</span>
        </div>
        <div class="text-xs text-slate-400 flex items-center justify-between mt-1">
          <span>DS18B20 Probe:</span>
          <span class="font-mono text-cyan-400">{data && data.ds18b20_temp > -100 ? `${data.ds18b20_temp.toFixed(1)}°C` : 'N/A'}</span>
        </div>
      </div>
      <span class="text-[10px] text-slate-500">BME280 / BMP280</span>
    </div>

    <!-- Humidity -->
    <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between">
      <div class="flex items-center justify-between text-slate-400 text-xs">
        <span>Humidity</span>
        <Droplets class="w-4 h-4 text-blue-400" />
      </div>
      <div class="my-2">
        <div class="text-2xl font-black text-slate-100 font-mono">
          {data ? data.bme_hum.toFixed(1) : '—'} <span class="text-sm font-normal text-slate-400">%</span>
        </div>
        <p class="text-xs text-slate-400 mt-1">Relative Humidity</p>
      </div>
      <span class="text-[10px] text-slate-500">BME280 Sensor</span>
    </div>

    <!-- Pressure -->
    <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between">
      <div class="flex items-center justify-between text-slate-400 text-xs">
        <span>Pressure</span>
        <Gauge class="w-4 h-4 text-indigo-400" />
      </div>
      <div class="my-2">
        <div class="text-2xl font-black text-slate-100 font-mono">
          {data ? data.bme_press.toFixed(1) : '—'} <span class="text-sm font-normal text-slate-400">hPa</span>
        </div>
        <p class="text-xs text-slate-400 mt-1">Barometric</p>
      </div>
      <span class="text-[10px] text-slate-500">I2C Bus</span>
    </div>

    <!-- Soil Moisture -->
    <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between">
      <div class="flex items-center justify-between text-slate-400 text-xs">
        <span>Soil Moisture</span>
        <Droplets class="w-4 h-4 text-emerald-400" />
      </div>
      <div class="my-2">
        <div class="text-2xl font-black text-slate-100 font-mono">
          {data ? data.soil_moist : '—'} <span class="text-sm font-normal text-slate-400">%</span>
        </div>
        <p class="text-xs text-slate-400 font-mono mt-1">ADC: {data?.soil_raw_mv ?? '—'} mV</p>
      </div>
      <span class="text-[10px] text-slate-500">GPIO13 Analog</span>
    </div>
  </div>

  <!-- RS485 Wind Sensors -->
  <section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3">
    <div class="flex items-center justify-between text-xs text-slate-400">
      <div class="flex items-center gap-1.5 font-semibold text-slate-300 text-sm">
        <Wind class="w-4 h-4 text-cyan-400" />
        <span>RS485 Modbus Wind Station</span>
      </div>
      <span class="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-400">UART1 @ 9600 Baud</span>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <span class="text-xs text-slate-400">Wind Speed (ID 1)</span>
        <div class="text-2xl font-black text-slate-100 font-mono mt-0.5">
          {data && data.wind_speed >= 0 ? data.wind_speed.toFixed(1) : 'Timeout'}
          <span class="text-sm font-normal text-slate-400">m/s</span>
        </div>
      </div>

      <div>
        <span class="text-xs text-slate-400">Wind Direction (ID 2)</span>
        <div class="flex items-center gap-2 mt-0.5">
          <div class="text-2xl font-black text-slate-100 font-mono">
            {data && data.wind_dir <= 360 ? `${data.wind_dir}°` : 'Timeout'}
          </div>
          {#if data && data.wind_dir <= 360}
            <span class="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 text-xs font-bold font-mono">
              {getWindDirectionCardinal(data.wind_dir)}
            </span>
          {/if}
        </div>
      </div>
    </div>
  </section>

  <!-- Rain Gauge -->
  <section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex items-center justify-between">
    <div>
      <div class="text-xs text-slate-400">Rain Gauge (Reed Switch Interrupt)</div>
      <div class="text-2xl font-black text-slate-100 font-mono mt-1">
        {data?.rain_mm?.toFixed(2) ?? '0.00'} <span class="text-sm font-normal text-slate-400">mm</span>
        <span class="text-xs text-slate-400 font-normal ml-1">({data?.rain_tips ?? 0} tips)</span>
      </div>
    </div>
    <button
      onclick={resetRain}
      disabled={resettingRain}
      class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 border border-slate-700 transition-colors"
    >
      {resettingRain ? 'Resetting...' : 'Reset Rain'}
    </button>
  </section>

  <!-- Hardware Controls & Diagnostics -->
  <section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3">
    <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hardware Testing & Controls</h2>

    <div class="grid grid-cols-2 gap-3">
      <!-- MOSFET Toggle -->
      <button
        onclick={toggleMosfet}
        disabled={togglingMosfet}
        class="flex items-center justify-center gap-2 p-3 rounded-xl border font-medium text-xs transition-colors {data?.mosfet_on ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20' : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:bg-slate-800'}"
      >
        <Power class="w-4 h-4 {data?.mosfet_on ? 'text-cyan-400' : 'text-slate-500'}" />
        <span>12V_SW MOSFET: {data?.mosfet_on ? 'ON' : 'OFF'}</span>
      </button>

      <!-- I2C Scanner -->
      <button
        onclick={scanI2c}
        disabled={scanningI2c}
        class="flex items-center justify-center gap-2 p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-medium text-xs transition-colors"
      >
        <Search class="w-4 h-4 text-cyan-400 {scanningI2c ? 'animate-spin' : ''}" />
        <span>{scanningI2c ? 'Scanning...' : 'Scan I2C Bus'}</span>
      </button>
    </div>

    <!-- I2C Results -->
    {#if i2cDevices}
      <div class="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono">
        <span class="text-slate-400">I2C Detected:</span>
        {#if i2cDevices.length === 0}
          <span class="text-amber-400 ml-2">No I2C devices found</span>
        {:else}
          <div class="flex flex-wrap gap-1.5 mt-2">
            {#each i2cDevices as dev}
              <span class="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">{dev}</span>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </section>

  <!-- WiFi Configuration (Dual Mode) -->
  <section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3">
    <button
      onclick={() => (showWifiSettings = !showWifiSettings)}
      class="w-full flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider"
    >
      <div class="flex items-center gap-1.5">
        <Wifi class="w-4 h-4 text-cyan-400" />
        <span>Connect to Home/Office WiFi (STA Mode)</span>
      </div>
      <span class="text-cyan-400 font-mono text-[10px]">{showWifiSettings ? '▲ Hide' : '▼ Setup'}</span>
    </button>

    {#if showWifiSettings}
      <div class="space-y-3 pt-2">
        <p class="text-xs text-slate-400">
          Connect the ESP32 to your home router so you can access <a href="http://weather.local" class="text-cyan-400 font-mono underline">http://weather.local</a> from any PC or phone on your local network.
        </p>

        <div>
          <label class="block text-[11px] text-slate-400 mb-1">WiFi Network Name (SSID)</label>
          <input
            type="text"
            bind:value={wifiSsid}
            placeholder="MyHomeWiFi"
            class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div>
          <label class="block text-[11px] text-slate-400 mb-1">WiFi Password</label>
          <input
            type="password"
            bind:value={wifiPass}
            placeholder="Password"
            class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
          />
        </div>

        <button
          onclick={saveWifi}
          class="w-full py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors"
        >
          Save & Connect
        </button>

        {#if wifiSaved}
          <p class="text-xs text-emerald-400 text-center">Settings saved to NVS! Connecting to WiFi...</p>
        {/if}
      </div>
    {/if}
  </section>

  <!-- Footer -->
  <footer class="text-center text-[11px] text-slate-500 py-2">
    ESP32-S3 N16R8 · Weather Station Research Node · Firmware v1.1.0-e22
  </footer>
</div>
