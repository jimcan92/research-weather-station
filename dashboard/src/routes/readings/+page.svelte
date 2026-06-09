<script lang="ts">
  import { onMount } from 'svelte';
  import { Thermometer, Droplets, Wind, CloudRain, Signal } from '@lucide/svelte';
  import { 
    formatTemp, formatHumidity, formatPressure, formatSpeed,
    formatDate, batteryColor, formatVoltage 
  } from '$lib/utils.js';

  interface Reading {
    id: number;
    node_id: number;
    node_name: string | null;
    temperature: string | null;
    humidity: string | null;
    pressure: string | null;
    battery_v: string | null;
    wind_speed: string | null;
    wind_dir: number | null;
    rain_mm: string | null;
    soil_moisture: string | null;
    rssi: number | null;
    received_at: string;
  }

  let readings = $state<Reading[]>([]);
  let loading = $state(true);
  let error = $state('');

  let page = $state(1);
  let totalReadings = $state(0);
  const perPage = 20;
  let totalPages = $derived(Math.ceil(totalReadings / perPage) || 1);

  async function loadReadings() {
    loading = true;
    error = '';
    try {
      const res = await fetch(`/api/readings?page=${page}&limit=${perPage}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      readings = json.readings ?? [];
      totalReadings = json.total ?? 0;
    } catch (e: any) {
      error = e.message || 'Failed to load';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadReadings();
  });

  function prevPage() { if (page > 1) { page--; loadReadings(); } }
  function nextPage() { if (page < totalPages) { page++; loadReadings(); } }
</script>

<svelte:head>
  <title>Readings — Weather Station</title>
</svelte:head>

<div class="mb-6">
  <h2 class="text-xl font-bold text-gray-900">Sensor Readings</h2>
  <p class="text-sm text-muted-foreground mt-1">{totalReadings.toLocaleString()} total · Page {page} of {totalPages}</p>
</div>

{#if loading}
  <div class="flex items-center justify-center h-64">
    <div class="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
  </div>
{:else if error}
  <div class="bg-red-50 text-red-700 p-4 rounded-lg">{error}</div>
{:else if !readings.length}
  <div class="bg-white rounded-lg border border-border p-12 text-center">
    <CloudRain class="w-12 h-12 text-gray-300 mx-auto mb-3" />
    <p class="text-gray-500">No readings recorded yet.</p>
  </div>
{:else}
  <div class="bg-white rounded-lg border border-border overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border bg-gray-50">
            <th class="text-left px-4 py-3 font-medium text-muted-foreground">Time</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground">Node</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Thermometer class="w-3.5 h-3.5 inline" /> Temp</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Droplets class="w-3.5 h-3.5 inline" /> Hum</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground">Press</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Wind class="w-3.5 h-3.5 inline" /> Wind</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><CloudRain class="w-3.5 h-3.5 inline" /> Rain</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground">Battery</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Signal class="w-3.5 h-3.5 inline" /> RSSI</th>
          </tr>
        </thead>
        <tbody>
          {#each readings as r}
            <tr class="border-b border-border hover:bg-gray-50 transition-colors">
              <td class="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">{formatDate(r.received_at)}</td>
              <td class="px-4 py-2.5">
                <a href="/nodes/{r.node_id}" class="text-primary hover:underline font-medium">
                  {r.node_name || `Node ${r.node_id}`}
                </a>
              </td>
              <td class="px-4 py-2.5">{formatTemp(r.temperature)}</td>
              <td class="px-4 py-2.5">{formatHumidity(r.humidity)}</td>
              <td class="px-4 py-2.5 text-xs">{r.pressure ? `${Number(r.pressure).toFixed(0)} hPa` : '—'}</td>
              <td class="px-4 py-2.5 text-xs">
                {formatSpeed(r.wind_speed)}
                {#if r.wind_dir != null}<span class="text-muted-foreground">@{r.wind_dir}°</span>{/if}
              </td>
              <td class="px-4 py-2.5 text-xs">{r.rain_mm ? `${Number(r.rain_mm).toFixed(1)} mm` : '—'}</td>
              <td class="px-4 py-2.5">
                <span class={batteryColor(r.battery_v ? Number(r.battery_v) : null)}>
                  {formatVoltage(r.battery_v)}
                </span>
              </td>
              <td class="px-4 py-2.5 text-xs">{r.rssi != null ? `${r.rssi} dBm` : '—'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    {#if totalPages > 1}
      <div class="flex items-center justify-between px-4 py-3 border-t border-border bg-gray-50">
        <p class="text-xs text-muted-foreground">
          {(page - 1) * perPage + 1}–{Math.min(page * perPage, totalReadings)} of {totalReadings.toLocaleString()}
        </p>
        <div class="flex gap-2">
          <button
            onclick={prevPage}
            disabled={page <= 1}
            class="px-3 py-1.5 text-xs rounded-md border border-border bg-white hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <span class="px-3 py-1.5 text-xs text-muted-foreground">{page} / {totalPages}</span>
          <button
            onclick={nextPage}
            disabled={page >= totalPages}
            class="px-3 py-1.5 text-xs rounded-md border border-border bg-white hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    {/if}
  </div>
{/if}
