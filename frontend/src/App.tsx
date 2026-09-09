import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar, NavTab } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Workbench } from './pages/Workbench';
import { Knowledge } from './pages/Knowledge';
import { AuditLogs } from './pages/AuditLogs';
import { SystemStatus } from './components/SystemStatus';
import { SovereigntyPanel } from './components/SovereigntyPanel';
import { NetworkMonitor } from './components/NetworkMonitor';
import { ModelStatus } from './components/ModelStatus';
import { api } from './services/api';
import { HealthResponse, NetworkStatus, ToolDefinition } from './types/api';
import { Layers } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('workbench');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [network, setNetwork] = useState<NetworkStatus | null>(null);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedTaskText, setSelectedTaskText] = useState<string>('');

  const fetchSystemData = useCallback(async () => {
    setLoading(true);
    try {
      const [healthData, netData, toolsData] = await Promise.allSettled([
        api.getHealth(),
        api.getNetworkStatus(),
        api.getAgentTools(),
      ]);

      if (healthData.status === 'fulfilled') {
        setHealth(healthData.value);
      }
      if (netData.status === 'fulfilled') {
        setNetwork(netData.value);
      }
      if (toolsData.status === 'fulfilled') {
        setTools(toolsData.value);
      }
    } catch (err) {
      console.error('Failed to load system data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSystemData();
    const interval = setInterval(fetchSystemData, 10000);
    return () => clearInterval(interval);
  }, [fetchSystemData]);

  const handleSelectPresetAndRun = (taskText: string) => {
    setSelectedTaskText(taskText);
    setCurrentTab('workbench');
  };

  return (
    <div className="app-container">
      <Header
        health={health}
        network={network}
        loading={loading}
        onRefresh={fetchSystemData}
      />

      <div className="app-body">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          toolCount={tools.length}
        />

        <main className="main-content">
          {currentTab === 'dashboard' && (
            <Dashboard
              health={health}
              network={network}
              tools={tools}
              loading={loading}
              onNavigate={setCurrentTab}
              onSelectPresetAndRun={handleSelectPresetAndRun}
            />
          )}

          {currentTab === 'workbench' && (
            <Workbench initialTask={selectedTaskText} />
          )}

          {currentTab === 'knowledge' && <Knowledge />}

          {currentTab === 'network' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <NetworkMonitor />
              <SovereigntyPanel network={network} loading={loading} />
            </div>
          )}

          {currentTab === 'audit_logs' && <AuditLogs />}

          {currentTab === 'system' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <NetworkMonitor />
              <SovereigntyPanel network={network} loading={loading} />
              <SystemStatus health={health} />
              <ModelStatus />


              {/* Registered Tools Details */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <Layers size={15} color="#38bdf8" />
                    <span>Registered Local Tools ({tools.length})</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Autonomous Tool Registry
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
                  {tools.map((tool, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 12px',
                        backgroundColor: '#070b14',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-brand-light)', fontFamily: 'var(--font-mono)' }}>
                          {tool.name}
                        </span>
                        <span style={{ fontSize: '10px', color: '#10b981', fontWeight: 600, backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '1px 5px', borderRadius: '3px' }}>
                          LOCAL
                        </span>
                      </div>
                      <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                        {tool.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
