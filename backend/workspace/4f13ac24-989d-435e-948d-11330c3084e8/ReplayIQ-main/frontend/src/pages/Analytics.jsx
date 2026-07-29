import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from '../services/axios';
import EmptyState from '../components/EmptyState';

const Analytics = () => {
  const { activeProject } = useAuth();
  const navigate = useNavigate();

  // Analytics states
  const [summary, setSummary] = useState(null);
  const [methods, setMethods] = useState({});
  const [statusCodes, setStatusCodes] = useState({});
  const [slowRequests, setSlowRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchAnalytics = async () => {
    if (!activeProject) return;

    setLoading(true);
    setError('');
    try {
      // 1. Fetch summary stats
      const summaryRes = await axios.get(`/projects/${activeProject.id}/analytics/summary`);
      setSummary(summaryRes.data);

      // 2. Fetch HTTP methods distribution
      const methodsRes = await axios.get(`/projects/${activeProject.id}/analytics/methods`);
      setMethods(methodsRes.data.counts || {});

      // 3. Fetch status codes distribution
      const statusRes = await axios.get(`/projects/${activeProject.id}/analytics/status-codes`);
      setStatusCodes(statusRes.data.counts || {});

      // 4. Fetch slow requests (limit to 5)
      const slowRes = await axios.get(`/projects/${activeProject.id}/analytics/slow-requests`, {
        params: { limit: 5 }
      });
      setSlowRequests(slowRes.data.requests || []);
    } catch (err) {
      console.error(err);
      setError('Failed to load project analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [activeProject]);

  if (!activeProject) {
    return (
      <div style={{ padding: '40px 0' }}>
        <EmptyState
          title="No Project Workspace"
          description="Create or select a project to inspect REST analytics reports."
          actionText="Projects"
          onActionClick={() => navigate('/projects')}
          icon="📁"
        />
      </div>
    );
  }

  if (loading && !summary) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div 
          style={{
            width: '40px', height: '40px', border: '3px solid var(--border-color)',
            borderTopColor: 'var(--color-primary)', borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}
        />
      </div>
    );
  }

  // Calculate maximum values for relative progress bar scaling
  const maxMethodValue = Object.values(methods).length > 0 ? Math.max(...Object.values(methods)) : 1;
  const maxStatusValue = Object.values(statusCodes).length > 0 ? Math.max(...Object.values(statusCodes)) : 1;
  const maxSlowLatency = slowRequests.length > 0 ? Math.max(...slowRequests.map(r => r.response_time_ms)) : 1;

  // Resolve status code category color
  const getStatusColorClass = (code) => {
    const numeric = parseInt(code);
    if (numeric >= 200 && numeric < 300) return 'success';
    if (numeric >= 400 && numeric < 500) return 'warning';
    if (numeric >= 500) return 'danger';
    return '';
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
          Analytics
          </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Track response latency, HTTP verb volume, and error status code distribution.
        </p>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {summary && summary.total_requests === 0 ? (
        <EmptyState
          title="No Data Captured"
          description="We need logged REST transactions in this project workspace to calculate metrics and distributions."
          actionText="Inspect Logs"
          onActionClick={() => navigate('/logs')}
          icon="📈"
        />
      ) : (
        <>
          {/* Main Visual charts Grid */}
          <div 
            style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
              gap: '24px', marginBottom: '32px'
            }}
          >
            {/* HTTP Status Code Distribution */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">HTTP Status Codes</h3>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.keys(statusCodes).length === 0 ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '20px' }}>
                    No status codes logged.
                  </div>
                ) : (
                  Object.keys(statusCodes).map((code) => {
                    const count = statusCodes[code];
                    const percent = maxStatusValue > 0 ? (count / maxStatusValue) * 100 : 0;
                    const colorClass = getStatusColorClass(code);

                    return (
                      <div key={code} className="analytics-bar-group">
                        <div className="analytics-bar-label-row">
                          <span style={{ fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span 
                              style={{
                                width: '8px', height: '8px', borderRadius: '50%',
                                backgroundColor: colorClass === 'success' ? 'var(--color-success)' :
                                                colorClass === 'warning' ? 'var(--color-warning)' :
                                                colorClass === 'danger' ? 'var(--color-danger)' : 'var(--text-muted)'
                              }}
                            />
                            {code}
                          </span>
                          <span style={{ color: 'var(--text-secondary)' }}>
                            {count} requests
                          </span>
                        </div>
                        <div className="analytics-bar-bg">
                          <div 
                            className={`analytics-bar-fill ${colorClass}`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* HTTP Method Distribution */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">HTTP Verbs</h3>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.keys(methods).length === 0 ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '20px' }}>
                    No request methods logged.
                  </div>
                ) : (
                  Object.keys(methods).map((method) => {
                    const count = methods[method];
                    const percent = maxMethodValue > 0 ? (count / maxMethodValue) * 100 : 0;
                    
                    return (
                      <div key={method} className="analytics-bar-group">
                        <div className="analytics-bar-label-row">
                          <span style={{ fontWeight: '600' }}>
                            {method}
                          </span>
                          <span style={{ color: 'var(--text-secondary)' }}>
                            {count} requests
                          </span>
                        </div>
                        <div className="analytics-bar-bg">
                          <div 
                            className="analytics-bar-fill" 
                            style={{ 
                              width: `${percent}%`,
                              backgroundColor: method === 'GET' ? 'var(--color-primary)' :
                                              method === 'POST' ? 'var(--color-success)' :
                                              method === 'PUT' ? 'var(--color-warning)' : 'var(--text-muted)'
                            }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Slow Request Latency Inspector Card */}
          <div className="card" style={{ marginBottom: '32px' }}>
            <div className="card-header">
              <h3 className="card-title">Slowest Endpoints Latency Inspector</h3>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {slowRequests.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '20px' }}>
                  No latency records found.
                </div>
              ) : (
                slowRequests.map((req, idx) => {
                  const percent = maxSlowLatency > 0 ? (req.response_time_ms / maxSlowLatency) * 100 : 0;
                  return (
                    <div key={`${req.url}-${idx}`} className="analytics-bar-group">
                      <div className="analytics-bar-label-row">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                          <span className={`badge badge-${req.method.toLowerCase()}`} style={{ minWidth: '60px', justifyContent: 'center' }}>
                            {req.method}
                          </span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                            {req.url}
                          </span>
                        </div>
                        <span style={{ fontWeight: '700', color: req.response_time_ms > 200 ? 'var(--color-warning)' : 'inherit' }}>
                          {req.response_time_ms} ms
                        </span>
                      </div>
                      <div className="analytics-bar-bg">
                        <div 
                          className="analytics-bar-fill"
                          style={{ 
                            width: `${percent}%`,
                            backgroundColor: req.response_time_ms > 500 ? 'var(--color-danger)' :
                                            req.response_time_ms > 200 ? 'var(--color-warning)' : 'var(--color-success)'
                          }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Analytics;
