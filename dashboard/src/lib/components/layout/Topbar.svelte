<script lang="ts">
  import { page } from '$app/stores';
  import { 
    ArrowLeft, Search, Bell, Plus, Menu
  } from '@lucide/svelte';

  let { onToggleSidebar }: { onToggleSidebar?: () => void } = $props();

  // Build breadcrumbs from pathname
  let breadcrumbs = $derived.by(() => {
    const path = $page.url.pathname;
    if (path === '/') return [{ label: 'Overview', href: '/' }];

    const segments = path.split('/').filter(Boolean);
    const crumbs = [{ label: 'Home', href: '/' }];

    let accumulated = '';
    for (const seg of segments) {
      accumulated += '/' + seg;
      let label = seg.charAt(0).toUpperCase() + seg.slice(1);
      // Replace ID segments
      if (/^\d+$/.test(seg)) label = 'Details';
      crumbs.push({ label, href: accumulated });
    }
    return crumbs;
  });

  function goBack() {
    history.back();
  }
</script>

<header class="h-14 bg-white border-b border-border flex items-center px-4 gap-4 sticky top-0 z-20">
  <!-- Left: Hamburger + Back + Breadcrumbs -->
  <div class="flex items-center gap-2 flex-1 min-w-0">
    <button
      onclick={onToggleSidebar}
      class="p-1.5 rounded-md hover:bg-gray-100 transition-colors lg:hidden"
      aria-label="Toggle sidebar"
    >
      <Menu class="w-5 h-5 text-gray-500" />
    </button>

    <button
      onclick={goBack}
      class="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
      aria-label="Go back"
    >
      <ArrowLeft class="w-4 h-4 text-gray-400" />
    </button>

    <nav class="flex items-center gap-1 text-sm min-w-0" aria-label="Breadcrumb">
      {#each breadcrumbs as crumb, i}
        {#if i > 0}
          <span class="text-gray-300 mx-1">/</span>
        {/if}
        {#if i === breadcrumbs.length - 1}
          <span class="text-gray-900 font-medium truncate">{crumb.label}</span>
        {:else}
          <a href={crumb.href} class="text-gray-500 hover:text-gray-700 transition-colors truncate">
            {crumb.label}
          </a>
        {/if}
      {/each}
    </nav>
  </div>

  <!-- Right: Search + Notifications + Add -->
  <div class="flex items-center gap-2">
    <button class="p-1.5 rounded-md hover:bg-gray-100 transition-colors" aria-label="Search">
      <Search class="w-4 h-4 text-gray-400" />
    </button>
    <button class="p-1.5 rounded-md hover:bg-gray-100 transition-colors relative" aria-label="Notifications">
      <Bell class="w-4 h-4 text-gray-400" />
      <span class="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full"></span>
    </button>
    <button class="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
      <Plus class="w-4 h-4" />
      Add Node
    </button>
  </div>
</header>
