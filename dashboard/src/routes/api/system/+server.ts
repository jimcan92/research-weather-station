import { json } from '@sveltejs/kit';
import si from 'systeminformation';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
  try {
    const [cpu, mem, disks, osInfo, currentLoad, time] = await Promise.all([
      si.cpu(),
      si.mem(),
      si.fsSize(),
      si.osInfo(),
      si.currentLoad(),
      si.time(),
    ]);

    // Root disk
    const rootDisk = disks.find(d => d.mount === '/') || disks[0];

    // CPU model (shorten)
    const cpuModel = cpu.brand.replace(/CPU|Processor|with Radeon|Graphics/g, '').replace(/\s+/g, ' ').trim();

    return json({
      system: {
        hostname: osInfo.hostname,
        platform: osInfo.platform,
        distro: osInfo.distro,
        arch: osInfo.arch,
        uptime: time.uptime, // seconds
      },
      cpu: {
        model: cpuModel,
        cores: cpu.cores,
        physicalCores: cpu.physicalCores,
        speed: cpu.speed,
        load: Math.round(currentLoad.currentLoad), // percentage
        loadUser: Math.round(currentLoad.currentLoadUser),
        loadSystem: Math.round(currentLoad.currentLoadSystem),
      },
      memory: {
        total: mem.total,
        used: mem.total - mem.available,  // real used (excludes buffers/cache)
        free: mem.free,
        available: mem.available,
        percent: Math.round(((mem.total - mem.available) / mem.total) * 100),
      },
      disk: rootDisk ? {
        fs: rootDisk.fs,
        size: rootDisk.size,
        used: rootDisk.used,
        available: rootDisk.available,
        percent: rootDisk.use,
        mount: rootDisk.mount,
      } : null,
    });
  } catch (err: any) {
    console.error('API /system error:', err);
    return json({ error: err.message }, { status: 500 });
  }
};
