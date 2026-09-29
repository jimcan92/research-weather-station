<script lang="ts">
  import Sidebar from './Sidebar.svelte';
  import Topbar from './Topbar.svelte';
  import { cn } from '$lib/utils.js';

  let { children }: { children: import('svelte').Snippet } = $props();
  let sidebarOpen = $state(false);

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }
</script>

<div class="flex h-screen">
  <!-- Desktop sidebar (always visible) -->
  <div class="hidden lg:block">
    <Sidebar />
  </div>

  <!-- Mobile overlay -->
  {#if sidebarOpen}
    <div
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      onclick={toggleSidebar}
      role="presentation"
    ></div>
    <div class="fixed inset-y-0 left-0 z-50 lg:hidden">
      <Sidebar />
    </div>
  {/if}

  <!-- Main content -->
  <div class="flex-1 flex flex-col lg:ml-64 min-h-screen">
    <Topbar onToggleSidebar={toggleSidebar} />
    <main class="flex-1 p-6 overflow-auto">
      {@render children()}
    </main>
  </div>
</div>
