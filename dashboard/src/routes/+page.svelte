<script lang="ts">
  import { onMount } from 'svelte';
  import { Thermometer, Droplets, Wind, CloudRain, Zap, MapPin, Activity } from '@lucide/svelte';
  import { formatTemp, formatHumidity, formatSpeed, formatDate, batteryColor } from '$lib/utils.js';

  interface LatestReading {
    node_id: number;
    node_name: string;
    temperature: string | null;
    humidity: string | null;
    pressure: string | null;
    battery_v: string | null;
    wind_speed: string | null;
    rain_mm: string | null;
    received_at: string;
  }

  interface OverviewData {
    totalNodes: number;
    activeNodes: number;
    latestReadings: LatestReading[];
    todayStats: { readings: number; avgTemp: string; totalRain: string };
  }

  let data = $state<OverviewData | null>(null);
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    try {
      const res = await fetch('/api/readings?limit=5');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      data = {
        totalNodes: json.totalNodes ?? 0,
        activeNodes: json.activeNodes ?? 0,
        latestReadings: json.latestReadings ?? [],
        todayStats: json.todayStats ?? { readings: 0, avgTemp: '—', totalRain: '—' },
      };
    } catch (e: any) {
      error = e.message || 'Failed to load';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Overview — Weather Station</title>
</svelte:head>

{#if loading}
  <div class="flex items-center justify-center h-64">
    <div class="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
  </div>
{:else if error}
  <div class="bg-red-50 text-red-700 p-4 rounded-lg">
    <p class="font-medium">Connection Error</p>
    <p class="text-sm mt-1">{error}</p>
    <p class="text-sm mt-2 text-red-500">Make sure the ingestor is running and DATABASE_URL is set.</p>
  </div>
{:else}
  <!-- Stats Cards -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-muted-foreground">Active Nodes</p>
          <p class="text-2xl font-bold mt-1">{data?.activeNodes ?? 0}<span class="text-sm font-normal text-muted-foreground"> / {data?.totalNodes ?? 0}</span></p>
        </div>
        <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
          <MapPin class="w-5 h-5 text-primary" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-muted-foreground">Today's Readings</p>
          <p class="text-2xl font-bold mt-1">{data?.todayStats.readings ?? 0}</p>
        </div>
        <div class="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
          <Activity class="w-5 h-5 text-purple-500" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-muted-foreground">Avg Temperature</p>
          <p class="text-2xl font-bold mt-1">{data?.todayStats.avgTemp ?? '—'}<span class="text-sm font-normal text-muted-foreground"> °C</span></p>
        </div>
        <div class="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
          <Thermometer class="w-5 h-5 text-orange-500" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-muted-foreground">Rain Today</p>
          <p class="text-2xl font-bold mt-1">{data?.todayStats.totalRain ?? '—'}<span class="text-sm font-normal text-muted-foreground"> mm</span></p>
        </div>
        <div class="w-10 h-10 bg-cyan-50 rounded-lg flex items-center justify-center">
          <CloudRain class="w-5 h-5 text-cyan-500" />
        </div>
      </div>
    </div>
  </div>

  <!-- Latest Readings Table -->
  <div class="bg-white rounded-lg border border-border">
    <div class="px-5 py-4 border-b border-border">
      <h2 class="font-semibold text-gray-900">Latest Readings</h2>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border bg-gray-50">
            <th class="text-left px-4 py-3 font-medium text-muted-foreground">Node</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Thermometer class="w-3.5 h-3.5 inline mr-1" />Temp</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Droplets class="w-3.5 h-3.5 inline mr-1" />Humidity</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Wind class="w-3.5 h-3.5 inline mr-1" />Wind</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground"><Zap class="w-3.5 h-3.5 inline mr-1" />Battery</th>
            <th class="text-left px-4 py-3 font-medium text-muted-foreground">Received</th>
          </tr>
        </thead>
        <tbody>
          {#if !data?.latestReadings?.length}
            <tr>
              <td colspan="6" class="px-4 py-8 text-center text-muted-foreground">
                No readings yet. Deploy a node or publish a test packet.
              </td>
            </tr>
          {:else}
            {#each data.latestReadings as reading}
              <tr class="border-b border-border hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3">
                  <a href="/nodes/{reading.node_id}" class="text-primary hover:underline font-medium">
                    {reading.node_name || `Node ${reading.node_id}`}
                  </a>
                </td>
                <td class="px-4 py-3">{formatTemp(reading.temperature)}</td>
                <td class="px-4 py-3">{formatHumidity(reading.humidity)}</td>
                <td class="px-4 py-3">{formatSpeed(reading.wind_speed)}</td>
                <td class="px-4 py-3">
                  <span class={batteryColor(reading.battery_v ? Number(reading.battery_v) : null)}>
                    {reading.battery_v ? `${Number(reading.battery_v).toFixed(2)}V` : '—'}
                  </span>
                </td>
                <td class="px-4 py-3 text-muted-foreground text-xs">{formatDate(reading.received_at)}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>
{/if}
