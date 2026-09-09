import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { PlugZap, RefreshCw } from 'lucide-react';
import { TopBar } from './app/TopBar';
import { SideNav } from './app/SideNav';
import { CommandPalette } from './app/CommandPalette';
import { isRouteId, type RouteId } from './app/navigation';
import { ErrorBoundary } from './ui/ErrorBoundary';
import { Notice } from './ui/primitives';
import { ToastProvider } from './ui/toast';
import { Overview } from './pages/Overview';
import { Workbench } from './pages/Workbench';
import { Assistant } from './pages/Assistant';
import { Knowledge } from './pages/Knowledge';
import { Sovereignty } from './pages/Sovereignty';
import { AuditTrail } from './pages/AuditTrail';
import { GuidedDemo } from './pages/GuidedDemo';
import { api } from './services/api';
import type { HealthResponse, NetworkStatus, ToolDefinition } from './types/api';

const POLL_INTERVAL_MS = 10_000;

function readRouteFromHash(): RouteId {
  const raw = window.location.hash.replace(/^#\/?/, '').trim();
  return isRouteId(raw) ? raw : 'overview';
}

const AppShell: React.FC = () => {
  const [route, setRoute] = useState<RouteId>(readRouteFromHash);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [network, setNetwork] = useState<NetworkStatus | null>(null);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [backendReachable, setBackendReachable] = useState(true);
  const [navOpen, setNavOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [presetTask, setPresetTask] = useState('');

  /* ---- routing ---- */

  const navigate = useCallback((id: RouteId) => {
    window.location.hash = `#/${id}`;
    setRoute(id);
    setNavOpen(false);
    window.scrollTo({ top: 0 });
  }, []);

  useEffect(() => {
    /** Rewrites an empty or retired hash so the address bar matches the page shown. */
    const normalizeHash = () => {
      const raw = window.location.hash.replace(/^#\/?/, '').trim();
      if (!isRouteId(raw)) {
        window.location.replace(`${window.location.pathname}${window.location.search}#/overview`);
        return true;
      }
      return false;
    };

    const onHashChange = () => {
      if (!normalizeHash()) setRoute(readRouteFromHash());
    };

    window.addEventListener('hashchange', onHashChange);
    normalizeHash();
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  /* ---- system polling ---- */

  const loadSystemData = useCallback(async () => {
    setRefreshing(true);
    const [healthResult, networkResult, toolsResult] = await Promise.allSettled([
      api.getHealth(),
      api.getNetworkStatus(),
      api.getAgentTools(),
    ]);

    if (healthResult.status === 'fulfilled') {
      setHealth(healthResult.value);
      setBackendReachable(true);
    } else {
      setBackendReachable(false);
    }
    if (networkResult.status === 'fulfilled') setNetwork(networkResult.value);
    if (toolsResult.status === 'fulfilled') setTools(toolsResult.value);

    setRefreshing(false);
  }, []);

  useEffect(() => {
    loadSystemData();
    const timer = window.setInterval(loadSystemData, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [loadSystemData]);

  /* ---- keyboard shortcut ---- */

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  /* ---- derived ---- */

  const modelCount = useMemo(
    () => (health?.models ? Object.values(health.models).filter(Boolean).length : 0),
    [health],
  );

  const runPreset = useCallback(
    (task: string) => {
      setPresetTask(task);
      navigate('workbench');
    },
    [navigate],
  );

  const page = (() => {
    switch (route) {
      case 'workbench':
        return <Workbench presetTask={presetTask} onPresetConsumed={() => setPresetTask('')} />;
      case 'assistant':
        return <Assistant />;
      case 'knowledge':
        return <Knowledge />;
      case 'sovereignty':
        return <Sovereignty network={network} />;
      case 'audit':
        return <AuditTrail />;
      case 'demo':
        return <GuidedDemo />;
      case 'overview':
      default:
        return (
          <Overview
            health={health}
            network={network}
            tools={tools}
            backendReachable={backendReachable}
            onNavigate={navigate}
            onRunPreset={runPreset}
          />
        );
    }
  })();

  return (
    <div className="app">
      <TopBar
        health={health}
        network={network}
        backendReachable={backendReachable}
        refreshing={refreshing}
        onRefresh={loadSystemData}
        onOpenPalette={() => setPaletteOpen(true)}
        navOpen={navOpen}
        onToggleNav={() => setNavOpen((open) => !open)}
      />

      <div className="app-body">
        <SideNav
          current={route}
          onNavigate={navigate}
          toolCount={tools.length}
          modelCount={modelCount}
          open={navOpen}
          onClose={() => setNavOpen(false)}
        />

        <main className="main">
          <div className="main-inner">
            {!backendReachable && (
              <Notice
                tone="danger"
                icon={<PlugZap size={16} />}
                actions={
                  <button type="button" className="btn btn-secondary btn-sm" onClick={loadSystemData}>
                    <RefreshCw size={13} className={refreshing ? 'spin' : undefined} />
                    Retry
                  </button>
                }
              >
                <strong>Backend unreachable.</strong> Start the API with{' '}
                <code className="mono">python run.py</code> and this console will reconnect
                automatically.
              </Notice>
            )}

            <ErrorBoundary resetKey={route}>{page}</ErrorBoundary>
          </div>
        </main>
      </div>

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onNavigate={navigate}
      />
    </div>
  );
};

export const App: React.FC = () => (
  <ToastProvider>
    <AppShell />
  </ToastProvider>
);

export default App;
