<script lang="ts">
  import { page } from '$app/stores';
  import { cn } from '$lib/utils.js';
  import { 
    LayoutDashboard, MapPin, Table2, BarChart3, Settings,
    CloudRain, Thermometer, Wind, Droplets, Sun
  } from '@lucide/svelte';

  interface NavItem {
    label: string;
    href: string;
    icon: typeof LayoutDashboard;
    active?: boolean;
  }

  interface NavGroup {
    label: string;
    items: NavItem[];
  }

  const navGroups: NavGroup[] = [
    {
      label: 'Main',
      items: [
        { label: 'Overview', href: '/', icon: LayoutDashboard },
        { label: 'Sensor Nodes', href: '/nodes', icon: MapPin },
        { label: 'Readings', href: '/readings', icon: Table2 },
        { label: 'Charts', href: '/charts', icon: BarChart3 },
      ]
    },
    {
      label: 'Environment',
      items: [
        { label: 'Temperature', href: '/charts/temperature', icon: Thermometer },
        { label: 'Rainfall', href: '/charts/rainfall', icon: CloudRain },
        { label: 'Wind', href: '/charts/wind', icon: Wind },
        { label: 'Humidity', href: '/charts/humidity', icon: Droplets },
      ]
    }
  ];

  const adminGroup: NavGroup = {
    label: 'Administration',
    items: [
      { label: 'Settings', href: '/settings', icon: Settings },
    ]
  };

  let pathname = $derived($page.url.pathname);

  function isActive(href: string): boolean {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  }
</script>

<aside class="w-64 bg-sidebar text-sidebar-foreground flex flex-col h-screen fixed left-0 top-0 z-30">
  <!-- Branding -->
  <div class="px-5 py-4 border-b border-sidebar-accent">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
        <Sun class="w-5 h-5 text-white" />
      </div>
      <div>
        <h1 class="font-semibold text-sm">Weather Station</h1>
        <p class="text-xs text-gray-400">Cantila Research</p>
      </div>
    </div>
  </div>

  <!-- User info -->
  <div class="px-5 py-3 border-b border-sidebar-accent">
    <p class="text-sm font-medium">Jimboy Cantila</p>
    <p class="text-xs text-gray-400">Administrator</p>
  </div>

  <!-- Navigation -->
  <nav class="flex-1 overflow-y-auto py-3 px-3 space-y-4">
    {#each [...navGroups, adminGroup] as group}
      <div>
        <p class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
          {group.label}
        </p>
        {#each group.items as item}
          <a
            href={item.href}
            class={cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
              isActive(item.href)
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-gray-300 hover:bg-sidebar-accent hover:text-white'
            )}
          >
            <item.icon class="w-4 h-4" />
            {item.label}
          </a>
        {/each}
      </div>
    {/each}
  </nav>

  <!-- Profile dropdown area -->
  <div class="border-t border-sidebar-accent p-3">
    <div class="flex items-center gap-3 px-2 py-2 rounded-md hover:bg-sidebar-accent cursor-pointer transition-colors">
      <div class="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center text-xs font-bold text-primary">
        JC
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm truncate">Jimboy Cantila</p>
        <p class="text-xs text-gray-400 truncate">jimcan@coe-research</p>
      </div>
      <Settings class="w-4 h-4 text-gray-400" />
    </div>
  </div>
</aside>
