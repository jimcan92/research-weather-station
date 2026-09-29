<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Cpu, MemoryStick, HardDrive, Clock, Server, Container,
    Thermometer, Droplets, CloudRain, Activity, Zap, AlertTriangle
  } from '@lucide/svelte';

  // ── System ──
  interface SystemData {
    system: { hostname: string; platform: string; distro: string; arch: string; uptime: number };
    cpu: { model: string; cores: number; load: number };
    memory: { total: number; used: number; percent: number };
    disk: { size: number; used: number; percent: number; mount: string } | null;
  }

  // ── Docker ──
  interface ContainerInfo {
    name: string; image: string; state: string; uptime: string; ports: string;
  }

  // ── Weather ──
  interface WeatherMini {
    temperature: string; humidity: string; rain: string; battery: string;
    nodeName: string; updatedAt: string;
  }

  let sys = $state<SystemData | null>(null);
  let containers = $state<ContainerInfo[]>([]);
  let dockerAvailable = $state(false);
  let weather = $state<WeatherMini | null>(null);
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    try {
      const [sysRes, dockerRes, weatherRes] = await Promise.all([
        fetch('/api/system'),
        fetch('/api/docker'),
        fetch('/api/readings?limit=1'),
      ]);

      if (sysRes.ok) sys = await sysRes.json();

      if (dockerRes.ok) {
        const d = await dockerRes.json();
        containers = d.containers || [];
        dockerAvailable = d.dockerAvailable;
      }

      if (weatherRes.ok) {
        const w = await weatherRes.json();
        if (w.readings?.length) {
          const r = w.readings[0];
          weather = {
            temperature: r.temperature || '—',
            humidity: r.humidity || '—',
            rain: w.todayStats?.totalRain || '—',
            battery: r.battery_v || '—',
            nodeName: r.node_name || '—',
            updatedAt: r.received_at || '',
          };
        }
      }
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  // ── Formatters ──
  function fmtBytes(bytes: number): string {
    if (bytes >= 1e12) return (bytes / 1e12).toFixed(1) + ' TB';
    if (bytes >= 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
    if (bytes >= 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
    return (bytes / 1e3).toFixed(1) + ' KB';
  }

  function fmtUptime(sec: number): string {
    const d = Math.floor(sec / 86400);
    const h = Math.floor((sec % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    const m = Math.floor((sec % 3600) / 60);
    return `${h}h ${m}m`;
  }

  function fmtDate(iso: string): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('en-PH', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function stateColor(state: string): string {
    return state === 'running' ? 'bg-green-100 text-green-700' :
           state === 'exited' ? 'bg-gray-100 text-gray-600' :
           state === 'restarting' ? 'bg-yellow-100 text-yellow-700' :
           'bg-red-100 text-red-700';
  }

  function loadColor(pct: number): string {
    if (pct >= 90) return 'text-red-500';
    if (pct >= 70) return 'text-amber-500';
    return 'text-green-500';
  }
</script>

<svelte:head>
  <title>Server Dashboard — coe-research</title>
</svelte:head>

{#if loading}
  <div class="flex items-center justify-center h-64">
    <div class="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
  </div>
{:else if error}
  <div class="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
    <p class="font-medium">Failed to load</p>
    <p class="text-sm mt-1">{error}</p>
  </div>
{:else}
  <!-- System Stats -->
  <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">System Resources</h2>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <!-- CPU -->
    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between mb-2">
        <Cpu class="w-5 h-5 text-blue-500" />
        <span class="text-xs text-muted-foreground">{sys?.cpu?.cores ?? '?'} cores</span>
      </div>
      <p class="text-xs text-muted-foreground">CPU Load</p>
      <p class="text-2xl font-bold {sys?.cpu ? loadColor(sys.cpu.load) : ''}">{sys?.cpu?.load ?? '—'}%</p>
      <p class="text-xs text-muted-foreground mt-1 truncate" title={sys?.cpu?.model}>{sys?.cpu?.model ?? ''}</p>
    </div>

    <!-- Memory -->
    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between mb-2">
        <MemoryStick class="w-5 h-5 text-purple-500" />
        <span class="text-xs text-muted-foreground">{sys?.memory ? fmtBytes(sys.memory.total) : '?'}</span>
      </div>
      <p class="text-xs text-muted-foreground">Memory</p>
      <p class="text-2xl font-bold {sys?.memory ? loadColor(sys.memory.percent) : ''}">{sys?.memory?.percent ?? '—'}%</p>
      <div class="w-full bg-gray-100 rounded-full h-1.5 mt-2">
        <div class="bg-purple-500 h-1.5 rounded-full transition-all" style="width: {sys?.memory?.percent ?? 0}%"></div>
      </div>
    </div>

    <!-- Disk -->
    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between mb-2">
        <HardDrive class="w-5 h-5 text-amber-500" />
        <span class="text-xs text-muted-foreground">{sys?.disk?.mount ?? '/'}</span>
      </div>
      <p class="text-xs text-muted-foreground">Disk</p>
      <p class="text-2xl font-bold {sys?.disk ? loadColor(sys.disk.percent) : ''}">{sys?.disk?.percent ?? '—'}%</p>
      <div class="w-full bg-gray-100 rounded-full h-1.5 mt-2">
        <div class="bg-amber-500 h-1.5 rounded-full transition-all" style="width: {sys?.disk?.percent ?? 0}%"></div>
      </div>
    </div>

    <!-- Uptime -->
    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between mb-2">
        <Clock class="w-5 h-5 text-green-500" />
        <span class="text-xs text-muted-foreground">{sys?.system?.hostname ?? '—'}</span>
      </div>
      <p class="text-xs text-muted-foreground">Uptime</p>
      <p class="text-2xl font-bold">{sys?.system?.uptime ? fmtUptime(sys.system.uptime) : '—'}</p>
      <p class="text-xs text-muted-foreground mt-1">{sys?.system?.distro ?? ''}</p>
    </div>
  </div>

  <!-- Docker Containers -->
  <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Docker Containers</h2>
  {#if !dockerAvailable}
    <div class="bg-white rounded-lg border border-border p-6 text-center text-muted-foreground text-sm">
      Docker socket not available. Install Docker or add user to docker group.
    </div>
  {:else if containers.length === 0}
    <div class="bg-white rounded-lg border border-border p-6 text-center text-muted-foreground text-sm">
      No containers running. Start with <code class="bg-gray-100 px-1 rounded">docker compose up -d</code>
    </div>
  {:else}
    <div class="bg-white rounded-lg border border-border overflow-hidden mb-6">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border bg-gray-50">
            <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Container</th>
            <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Image</th>
            <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Status</th>
            <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Uptime</th>
            <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Ports</th>
          </tr>
        </thead>
        <tbody>
          {#each containers as c}
            <tr class="border-b border-border hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 font-medium">{c.name}</td>
              <td class="px-4 py-3 text-muted-foreground">{c.image}</td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium {stateColor(c.state)}">
                  <span class="w-1.5 h-1.5 rounded-full {c.state === 'running' ? 'bg-green-500' : 'bg-gray-400'}"></span>
                  {c.state}
                </span>
              </td>
              <td class="px-4 py-3 text-muted-foreground">{c.uptime}</td>
              <td class="px-4 py-3 text-muted-foreground text-xs">{c.ports || '—'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  <!-- Weather Mini Overview -->
  <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Weather Station — Latest</h2>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-muted-foreground">Temperature</p>
          <p class="text-2xl font-bold mt-1">{weather?.temperature ?? '—'}<span class="text-sm font-normal text-muted-foreground"> °C</span></p>
        </div>
        <div class="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
          <Thermometer class="w-5 h-5 text-orange-500" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-muted-foreground">Humidity</p>
          <p class="text-2xl font-bold mt-1">{weather?.humidity ?? '—'}<span class="text-sm font-normal text-muted-foreground"> %</span></p>
        </div>
        <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
          <Droplets class="w-5 h-5 text-blue-500" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-muted-foreground">Rain Today</p>
          <p class="text-2xl font-bold mt-1">{weather?.rain ?? '—'}<span class="text-sm font-normal text-muted-foreground"> mm</span></p>
        </div>
        <div class="w-10 h-10 bg-cyan-50 rounded-lg flex items-center justify-center">
          <CloudRain class="w-5 h-5 text-cyan-500" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-border p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-muted-foreground">Battery ({weather?.nodeName ?? '—'})</p>
          <p class="text-2xl font-bold mt-1">{weather?.battery ?? '—'}<span class="text-sm font-normal text-muted-foreground"> V</span></p>
        </div>
        <div class="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
          <Zap class="w-5 h-5 text-green-500" />
        </div>
      </div>
    </div>
  </div>

  {#if weather?.updatedAt}
    <p class="text-xs text-muted-foreground mt-2">Last updated: {fmtDate(weather.updatedAt)}</p>
  {/if}
{/if}
