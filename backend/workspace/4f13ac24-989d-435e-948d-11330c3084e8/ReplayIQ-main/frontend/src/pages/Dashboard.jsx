import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from '../services/axios';
import EmptyState from '../components/EmptyState';

const Dashboard = () => {
  const { user, activeProject } = useAuth();
  const [metrics, setMetrics] = useState({
    total_requests: 0,
    success_rate: 0,
    failed_requests: 0,
    avg_response_time_ms: 0,
  });
  const [recentLogs, setRecentLogs] = useState([]);
  const [recentTraffic, setRecentTraffic] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchDashboardData = async () => {
    if (!activeProject) return;

    setLoading(true);
    setError('');
    try {
      // 1. Fetch summary statistics
      const summaryRes = await axios.get(`/projects/${activeProject.id}/analytics/summary`);
      setMetrics(summaryRes.data);

      // 2. Fetch recent manual logs (limit to 5)
      const logsRes = await axios.get(`/projects/${activeProject.id}/logs`, {
        params: { page: 1, limit: 5 }
      });
      setRecentLogs(logsRes.data);

      // 3. Fetch recent captured request traffic (limit to 5)
      const trafficRes = await axios.get('/requests', {
        params: { limit: 5, project_id: activeProject.id }
      });
      setRecentTraffic(trafficRes.data);
    } catch (err) {
      console.error('Failed to load dashboard statistics', err);
      setError('Could not retrieve project logs. Please check your backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [activeProject]);

  if (!activeProject) {
    return (
      <div style={{ padding: '40px 0' }}>
        <EmptyState
          title="No Project Workspace Selected"
          description="Create or select a project to start capturing API request payloads, triggering replays, and running regression tests."
          actionText="Create Project"
          onActionClick={() => navigate('/projects')}
          icon="📁"
        />
      </div>
    );
  }

  // Loading spinner
  if (loading && metrics.total_requests === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div 
          style={{
            width: '40px', height: '40px', border: '3px solid var(--border-color)',
            borderTopColor: 'var(--color-primary)', borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}
        />
        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>
      </div>
    );
  }

  return (
    <div>
      {/* Welcome Back Hero */}
      <section style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
          Welcome back, {user?.full_name || 'Developer'}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Here is what's happening with <strong style={{ color: 'var(--text-primary)' }}>{activeProject.name}</strong>.
        </p>
      </section>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-title">Total Requests</span>
          <span className="metric-value">{metrics.total_requests}</span>
          <div className="metric-trend neutral">All time volume</div>
        </div>

        <div className="metric-card">
          <span className="metric-title">Success Rate</span>
          <span className="metric-value">
            {metrics.success_rate != null ? `${Number(metrics.success_rate).toFixed(1)}%` : '0.0%'}
          </span>
          <div className={`metric-trend ${metrics.success_rate >= 90 ? 'up' : 'down'}`}>
            {metrics.success_rate >= 90 ? '🟢 Excellent' : '🔴 Review logs'}
          </div>
        </div>

        <div className="metric-card">
          <span className="metric-title">Failed Requests</span>
          <span className="metric-value" style={{ color: metrics.failed_requests > 0 ? 'var(--color-danger)' : 'inherit' }}>
            {metrics.failed_requests}
          </span>
          <div className="metric-trend neutral">Non-2xx status codes</div>
        </div>

        <div className="metric-card">
          <span className="metric-title">Average Latency</span>
          <span className="metric-value">
            {metrics.avg_response_time_ms != null ? `${Number(metrics.avg_response_time_ms).toFixed(0)} ms` : '0 ms'}
          </span>
          <div className="metric-trend neutral">RTT execution time</div>
        </div>
      </div>

      {metrics.total_requests === 0 ? (
        <EmptyState
          title="No Logs Captured Yet"
          description="Start triggering API request transactions on your routes, or store manual mock request payloads to watch analytics updates."
          actionText="Import API Logs"
          onActionClick={() => navigate('/logs')}
          icon="⚡"
        />
      ) : (
        /* Double Column Grid: Recent Captured Traffic vs Recent Manual Logs */
        <div className="dashboard-details-grid">
          {/* Recent Manual Logs */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Recent Mock Logs</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/logs')}>
                View All
              </button>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
              {recentLogs.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '20px' }}>
                  No manual logs created.
                </div>
              ) : (
                recentLogs.map((log) => (
                  <div 
                    key={log.id} 
                    className="hover-lift"
                    onClick={() => navigate('/logs')}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: '8px',
                      backgroundColor: 'rgba(255, 255, 255, 0.005)', cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                      <span className={`badge badge-${log.method.toLowerCase()}`} style={{ minWidth: '60px', justifyContent: 'center' }}>
                        {log.method}
                      </span>
                      <span style={{ fontSize: '0.875rem', fontWeight: '500', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                        {log.url}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className={`badge ${log.status_code < 400 ? 'badge-success' : 'badge-danger'}`}>
                        {log.status_code}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {log.response_time_ms}ms
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Captured Traffic */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Recent Captured Traffic</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/logs')}>
                Inspect Traffic
              </button>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
              {recentTraffic.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '20px' }}>
                  No automatic traffic captured. Send requests with authorization header to record logs.
                </div>
              ) : (
                recentTraffic.map((traffic) => (
                  <div 
                    key={traffic.id}
                    className="hover-lift"
                    onClick={() => navigate('/logs')}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: '8px',
                      backgroundColor: 'rgba(255, 255, 255, 0.005)', cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                      <span className={`badge badge-${traffic.method.toLowerCase()}`} style={{ minWidth: '60px', justifyContent: 'center' }}>
                        {traffic.method}
                      </span>
                      <span style={{ fontSize: '0.875rem', fontWeight: '500', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                        {traffic.path}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className={`badge ${traffic.response_status < 400 ? 'badge-success' : 'badge-danger'}`}>
                        {traffic.response_status}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {Math.round(traffic.response_time_ms)}ms
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
