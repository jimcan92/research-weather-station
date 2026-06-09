<script lang="ts">
  import { onMount } from 'svelte';
  import { MapPin, Battery, Wifi, Activity, ChevronRight } from '@lucide/svelte';
  import { formatDate, batteryColor, formatTemp, formatHumidity } from '$lib/utils.js';

  interface NodeInfo {
    id: number;
    name: string;
    location: string | null;
    node_type: string;
    active: boolean;
    last_reading: {
      temperature: string | null;
      humidity: string | null;
      battery_v: string | null;
      rssi: number | null;
      received_at: string;
    } | null;
  }

  let nodes = $state<NodeInfo[]>([]);
  let loading = $state(true);
  let error = $state('');

  let page = $state(1);
  let totalNodes = $state(0);
  const perPage = 10;
  let totalPages = $derived(Math.ceil(totalNodes / perPage) || 1);

  async function loadNodes() {
    loading = true;
    error = '';
    try {
      const res = await fetch(`/api/nodes?page=${page}&limit=${perPage}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      nodes = json.nodes ?? [];
      totalNodes = json.total ?? 0;
    } catch (e: any) {
      error = e.message || 'Failed to load';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadNodes();
  });

  function prevPage() { if (page > 1) { page--; loadNodes(); } }
  function nextPage() { if (page < totalPages) { page++; loadNodes(); } }
</script>

<svelte:head>
  <title>Sensor Nodes — Weather Station</title>
</svelte:head>

<div class="mb-6">
  <h2 class="text-xl font-bold text-gray-900">Sensor Nodes</h2>
  <p class="text-sm text-muted-foreground mt-1">{totalNodes} registered · {page} of {totalPages} pages</p>
</div>

{#if loading}
  <div class="flex items-center justify-center h-64">
    <div class="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
  </div>
{:else if error}
  <div class="bg-red-50 text-red-700 p-4 rounded-lg">{error}</div>
{:else if !nodes.length}
  <div class="bg-white rounded-lg border border-border p-12 text-center">
    <MapPin class="w-12 h-12 text-gray-300 mx-auto mb-3" />
    <p class="text-gray-500">No sensor nodes registered yet.</p>
    <p class="text-sm text-gray-400 mt-1">Add nodes via the database seed or API.</p>
  </div>
{:else}
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {#each nodes as node}
      <a href="/nodes/{node.id}" class="bg-white rounded-lg border border-border p-5 hover:shadow-md hover:border-primary/30 transition-all block group">
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center {node.active ? 'bg-green-50' : 'bg-gray-100'}">
              <MapPin class="w-4 h-4 {node.active ? 'text-green-600' : 'text-gray-400'}" />
            </div>
            <div>
              <h3 class="font-medium text-gray-900 group-hover:text-primary transition-colors">{node.name}</h3>
              <p class="text-xs text-muted-foreground">{node.location || 'No location'}</p>
            </div>
          </div>
          <ChevronRight class="w-4 h-4 text-gray-300 group-hover:text-primary transition-colors" />
        </div>

        <div class="flex items-center gap-4 text-sm">
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
            {node.node_type}
          </span>
          <span class="flex items-center gap-1 {node.active ? 'text-green-600' : 'text-gray-400'}">
            <Activity class="w-3 h-3" />
            {node.active ? 'Active' : 'Inactive'}
          </span>
        </div>

        {#if node.last_reading}
          <div class="mt-4 pt-3 border-t border-border grid grid-cols-2 gap-2 text-xs">
            <div>
              <span class="text-muted-foreground">Temp </span>
              <span class="font-medium">{formatTemp(node.last_reading.temperature)}</span>
            </div>
            <div>
              <span class="text-muted-foreground">Humidity </span>
              <span class="font-medium">{formatHumidity(node.last_reading.humidity)}</span>
            </div>
            <div>
              <span class="text-muted-foreground">Battery </span>
              <span class={batteryColor(node.last_reading.battery_v ? Number(node.last_reading.battery_v) : null)}>
                {node.last_reading.battery_v ? `${Number(node.last_reading.battery_v).toFixed(2)}V` : '—'}
              </span>
            </div>
            <div class="text-muted-foreground">
              {formatDate(node.last_reading.received_at)}
            </div>
          </div>
        {:else}
          <div class="mt-4 pt-3 border-t border-border text-xs text-muted-foreground">
            No readings yet
          </div>
        {/if}
      </a>
    {/each}
  </div>

  <!-- Pagination -->
  {#if totalPages > 1}
    <div class="flex items-center justify-between mt-6">
      <p class="text-sm text-muted-foreground">
        Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, totalNodes)} of {totalNodes}
      </p>
      <div class="flex gap-2">
        <button
          onclick={prevPage}
          disabled={page <= 1}
          class="px-3 py-1.5 text-sm rounded-md border border-border hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Previous
        </button>
        <button
          onclick={nextPage}
          disabled={page >= totalPages}
          class="px-3 py-1.5 text-sm rounded-md border border-border hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  {/if}
{/if}
