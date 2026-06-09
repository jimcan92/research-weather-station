<script lang="ts">
  import { onMount } from 'svelte';
  import { BarChart3, Thermometer, CloudRain, Wind, Droplets } from '@lucide/svelte';

  interface DailyAgg {
    date: string;
    temp_avg: string | null;
    temp_max: string | null;
    temp_min: string | null;
    humidity_avg: string | null;
    rain_total: string | null;
    wind_max: string | null;
    reading_count: number;
  }

  let data = $state<DailyAgg[]>([]);
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    // For now, show a placeholder — charts will use a charting library later
    loading = false;
  });
</script>

<svelte:head>
  <title>Charts — Weather Station</title>
</svelte:head>

<div class="mb-6">
  <h2 class="text-xl font-bold text-gray-900">Charts & Analysis</h2>
  <p class="text-sm text-muted-foreground mt-1">Visualize sensor data trends</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
  <a href="/charts/temperature" class="bg-white rounded-lg border border-border p-6 hover:shadow-md hover:border-primary/30 transition-all group">
    <Thermometer class="w-8 h-8 text-orange-500 mb-3" />
    <h3 class="font-semibold text-gray-900 group-hover:text-primary transition-colors">Temperature Trends</h3>
    <p class="text-sm text-muted-foreground mt-1">Daily min, max, and average temperatures</p>
  </a>
  <a href="/charts/rainfall" class="bg-white rounded-lg border border-border p-6 hover:shadow-md hover:border-primary/30 transition-all group">
    <CloudRain class="w-8 h-8 text-blue-500 mb-3" />
    <h3 class="font-semibold text-gray-900 group-hover:text-primary transition-colors">Rainfall Accumulation</h3>
    <p class="text-sm text-muted-foreground mt-1">Daily rainfall totals and intensity</p>
  </a>
  <a href="/charts/wind" class="bg-white rounded-lg border border-border p-6 hover:shadow-md hover:border-primary/30 transition-all group">
    <Wind class="w-8 h-8 text-cyan-500 mb-3" />
    <h3 class="font-semibold text-gray-900 group-hover:text-primary transition-colors">Wind Analysis</h3>
    <p class="text-sm text-muted-foreground mt-1">Speed and direction distribution</p>
  </a>
  <a href="/charts/humidity" class="bg-white rounded-lg border border-border p-6 hover:shadow-md hover:border-primary/30 transition-all group">
    <Droplets class="w-8 h-8 text-blue-400 mb-3" />
    <h3 class="font-semibold text-gray-900 group-hover:text-primary transition-colors">Humidity & Pressure</h3>
    <p class="text-sm text-muted-foreground mt-1">Atmospheric humidity and barometric pressure</p>
  </a>
</div>
