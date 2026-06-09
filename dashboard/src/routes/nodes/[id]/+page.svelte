<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { 
    Thermometer, Droplets, Wind, CloudRain, Zap, MapPin, 
    Signal, Activity, Gauge, Navigation
  } from '@lucide/svelte';
  import { 
    formatTemp, formatHumidity, formatPressure, formatSpeed,
    formatDate, batteryColor, formatVoltage 
  } from '$lib/utils.js';

  let nodeId = $derived($page.params.id);

  interface NodeDetail {
    id: number;
    name: string;
    location: string | null;
    latitude: number | null;
    longitude: number | null;
    elevation_m: string | null;
    node_type: string;
    lora_spreading_factor: number;
    sleep_interval_s: number;
    active: boolean;
  }

  interface Reading {
    id: number;
    temperature: string | null;
    humidity: string | null;
    pressure: string | null;
    battery_v: string | null;
    wind_speed: string | null;
    wind_dir: number | null;
    rain_mm: string | null;
    soil_moisture: string | null;
    rssi: number | null;
    snr: string | null;
    received_at: string;
  }

  let node = $state<NodeDetail | null>(null);
  let readings = $state<Reading[]>([]);
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    try {
      const res = await fetch(`/api/nodes/${nodeId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      node = json.node;
      readings = json.recentReadings ?? [];
    } catch (e: any) {
      error = e.message || 'Failed to load';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>{node?.name || `Node ${nodeId}`} — Weather Station</title>
</svelte:head>

{#if loading}
  <div class="flex items-center justify-center h-64">
    <div class="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
  </div>
{:else if error}
  <div class="bg-red-50 text-red-700 p-4 rounded-lg">{error}</div>
{:else if node}
  <!-- Node Info Header -->
  <div class="bg-white rounded-lg border border-border p-5 mb-6">
    <div class="flex items-start justify-between">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <h2 class="text-xl font-bold text-gray-900">{node.name}</h2>
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs {node.active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}">
            <Activity class="w-3 h-3" />
            {node.active ? 'Active' : 'Inactive'}
          </span>
        </div>
        <div class="flex items-center gap-3 text-sm text-muted-foreground">
          {#if node.location}
            <span class="flex items-center gap-1"><MapPin class="w-3.5 h-3.5" /> {node.location}</span>
          {/if}
          <span>{node.node_type}</span>
          <span>SF{node.lora_spreading_factor}</span>
          <span>Sleep: {node.sleep_interval_s}s</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Latest Reading Cards -->
  {#if readings.length > 0}
    {@const latest = readings[0]}
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      <div class="bg-white rounded-lg border border-border p-3 text-center">
        <Thermometer class="w-4 h-4 text-orange-500 mx-auto mb-1" />
        <p class="text-lg font-bold">{formatTemp(latest.temperature)}</p>
        <p class="text-xs text-muted-foreground">Temperature</p>
      </div>
      <div class="bg-white rounded-lg border border-border p-3 text-center">
        <Droplets class="w-4 h-4 text-blue-500 mx-auto mb-1" />
        <p class="text-lg font-bold">{formatHumidity(latest.humidity)}</p>
        <p class="text-xs text-muted-foreground">Humidity</p>
      </div>
      <div class="bg-white rounded-lg border border-border p-3 text-center">
        <Gauge class="w-4 h-4 text-purple-500 mx-auto mb-1" />
        <p class="text-lg font-bold">{formatPressure(latest.pressure)}</p>
        <p class="text-xs text-muted-foreground">Pressure</p>
      </div>
      <div class="bg-white rounded-lg border border-border p-3 text-center">
        <Wind class="w-4 h-4 text-cyan-500 mx-auto mb-1" />
        <p class="text-lg font-bold">{formatSpeed(latest.wind_speed)}</p>
        {#if latest.wind_dir != null}
          <p class="text-xs text-muted-foreground">
            <Navigation class="w-3 h-3 inline" style="transform:rotate({latest.wind_dir}deg)" /> {latest.wind_dir}°
          </p>
        {:else}
          <p class="text-xs text-muted-foreground">Wind Speed</p>
        {/if}
      </div>
      <div class="bg-white rounded-lg border border-border p-3 text-center">
        <Zap class="w-4 h-4 mx-auto mb-1 {batteryColor(latest.battery_v ? Number(latest.battery_v) : null)}" />
        <p class="text-lg font-bold {batteryColor(latest.battery_v ? Number(latest.battery_v) : null)}">
          {formatVoltage(latest.battery_v)}
        </p>
        <p class="text-xs text-muted-foreground">Battery</p>
      </div>
      <div class="bg-white rounded-lg border border-border p-3 text-center">
        <Signal class="w-4 h-4 text-gray-400 mx-auto mb-1" />
        <p class="text-lg font-bold">{latest.rssi ?? '—'} dBm</p>
        <p class="text-xs text-muted-foreground">RSSI</p>
      </div>
    </div>
  {/if}

  <!-- Recent Readings Table -->
  <div class="bg-white rounded-lg border border-border">
    <div class="px-5 py-3 border-b border-border">
      <h3 class="font-semibold text-gray-900">Recent Readings</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border bg-gray-50">
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Time</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Temp</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Humidity</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Pressure</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Wind</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Rain</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">Battery</th>
            <th class="text-left px-4 py-2 font-medium text-muted-foreground">RSSI</th>
          </tr>
        </thead>
        <tbody>
          {#if !readings.length}
            <tr>
              <td colspan="8" class="px-4 py-8 text-center text-muted-foreground">No readings yet</td>
            </tr>
          {:else}
            {#each readings as r}
              <tr class="border-b border-border hover:bg-gray-50 transition-colors">
                <td class="px-4 py-2 text-xs text-muted-foreground whitespace-nowrap">{formatDate(r.received_at)}</td>
                <td class="px-4 py-2">{formatTemp(r.temperature)}</td>
                <td class="px-4 py-2">{formatHumidity(r.humidity)}</td>
                <td class="px-4 py-2 text-xs">{r.pressure ? `${Number(r.pressure).toFixed(0)} hPa` : '—'}</td>
                <td class="px-4 py-2 text-xs">
                  {formatSpeed(r.wind_speed)}
                  {#if r.wind_dir != null}<span class="text-muted-foreground"> @{r.wind_dir}°</span>{/if}
                </td>
                <td class="px-4 py-2 text-xs">{r.rain_mm ? `${Number(r.rain_mm).toFixed(1)} mm` : '—'}</td>
                <td class="px-4 py-2">
                  <span class={batteryColor(r.battery_v ? Number(r.battery_v) : null)}>
                    {formatVoltage(r.battery_v)}
                  </span>
                </td>
                <td class="px-4 py-2 text-xs text-muted-foreground">{r.rssi ?? '—'} dBm</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>
{/if}
