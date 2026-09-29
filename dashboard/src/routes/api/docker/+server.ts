import { json } from '@sveltejs/kit';
import { execSync } from 'child_process';
import type { RequestHandler } from './$types';

interface ContainerStatus {
  name: string;
  image: string;
  status: string;
  state: 'running' | 'exited' | 'restarting' | 'paused' | 'unknown';
  ports: string;
  uptime: string;
}

export const GET: RequestHandler = async () => {
  try {
    const output = execSync(
      `sg docker -c "docker ps -a --format '{{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.State}}\\t{{.Ports}}' --filter 'name=ws-'" 2>/dev/null || echo ""`,
      { encoding: 'utf-8', timeout: 5000 }
    ).trim();

    if (!output) {
      return json({ containers: [], dockerAvailable: false });
    }

    const containers: ContainerStatus[] = output.split('\n').filter(Boolean).map(line => {
      const [name, image, status, state, ports] = line.split('\t');
      // Extract uptime from status string like "Up 5 minutes"
      const uptimeMatch = status.match(/Up (.+)/);
      return {
        name: name || '',
        image: (image || '').replace(/:.*/, ''),
        status: status || '',
        state: (state || 'unknown') as ContainerStatus['state'],
        ports: (ports || '').replace(/0\.0\.0\.0:/g, '').replace(/, /g, ', '),
        uptime: uptimeMatch ? uptimeMatch[1] : '—',
      };
    });

    return json({ containers, dockerAvailable: true });
  } catch (err: any) {
    console.error('API /docker error:', err);
    return json({ containers: [], dockerAvailable: false, error: err.message });
  }
};
