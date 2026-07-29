import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from '../services/axios';
import EmptyState from '../components/EmptyState';
import Modal from '../components/Modal';

const ApiLogs = () => {
  const { activeProject } = useAuth();
  const navigate = useNavigate();

  // Tab State: 'mock' | 'traffic'
  const [activeTab, setActiveTab] = useState('mock');

  // Logs States
  const [logs, setLogs] = useState([]);
  const [traffic, setTraffic] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Pagination & Filtering States
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const limit = 10;

  const [search, setSearch] = useState('');
  const [methodFilter, setMethodFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Drawer detail states
  const [selectedItem, setSelectedItem] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState('request'); // 'request' | 'response'

  // Create Log Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [logForm, setLogForm] = useState({
    method: 'GET',
    url: '',
    request_headers: '{}',
    request_body: '{}',
    response_headers: '{}',
    response_body: '{}',
    status_code: 200,
    response_time_ms: 100,
  });

  // Load logs depending on selected tab, search, filters, and page
  const fetchLogs = async () => {
    if (!activeProject) return;
    setLoading(true);
    setError('');

    try {
      if (activeTab === 'mock') {
        const params = {
          page,
          limit,
          method: methodFilter || undefined,
          status_code: statusFilter ? parseInt(statusFilter) : undefined,
        };

        const res = await axios.get(`/projects/${activeProject.id}/logs`, { params });
        
        // Frontend local search filter since url filter on backend is not exposed directly
        let filtered = res.data;
        if (search) {
          filtered = filtered.filter(log => log.url.toLowerCase().includes(search.toLowerCase()));
        }

        setLogs(filtered);
        // Simple page count approximation based on limit
        setTotalPages(res.data.length < limit && page === 1 ? 1 : page + (res.data.length === limit ? 1 : 0));
      } else {
        const params = {
          skip: (page - 1) * limit,
          limit,
          method: methodFilter || undefined,
          status: statusFilter ? parseInt(statusFilter) : undefined,
          project_id: activeProject.id,
        };

        const res = await axios.get('/requests', { params });
        let filtered = res.data;
        if (search) {
          filtered = filtered.filter(item => item.path.toLowerCase().includes(search.toLowerCase()));
        }

        setTraffic(filtered);
        setTotalPages(res.data.length < limit && page === 1 ? 1 : page + (res.data.length === limit ? 1 : 0));
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch transaction logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
    fetchLogs();
  }, [activeProject, activeTab, methodFilter, statusFilter]);

  // Handle reload logs trigger manually or on search query submit
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchLogs();
  };

  // Open sliding details drawer
  const openDetails = (item) => {
    setSelectedItem(item);
    setDrawerTab('request');
    setDrawerOpen(true);
  };

  const closeDetails = () => {
    setDrawerOpen(false);
    setSelectedItem(null);
  };

  // Helper to parse string to clean format JSON
  const formatJSON = (val) => {
    if (!val) return 'null';
    if (typeof val === 'object') return JSON.stringify(val, null, 2);
    try {
      const parsed = JSON.parse(val);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return String(val);
    }
  };

  // Trigger Replay for Mock Logs
  const handleTriggerReplay = async () => {
    if (!selectedItem || activeTab !== 'mock') return;
    setLoading(true);
    try {
      const res = await axios.post(`/projects/${activeProject.id}/logs/${selectedItem.id}/replay`);
      const replayData = res.data;
      closeDetails();
      // Redirect to comparison screen for this replay ID
      navigate(`/replays?project_id=${activeProject.id}&log_id=${selectedItem.id}&replay_id=${replayData.id}`);
    } catch (err) {
      console.error(err);
      alert('Failed to trigger request replay. Ensure target URL is correct and backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Delete log entry
  const handleDeleteLog = async () => {
    if (!selectedItem || activeTab !== 'mock') return;
    if (!window.confirm('Delete this mock log payload permanently?')) return;
    try {
      await axios.delete(`/projects/${activeProject.id}/logs/${selectedItem.id}`);
      closeDetails();
      fetchLogs();
    } catch (err) {
      console.error(err);
      alert('Failed to delete log entry.');
    }
  };

  // Create Mock Log
  const handleCreateMockLog = async (e) => {
    e.preventDefault();
    if (!logForm.url.trim()) {
      alert('URL endpoint path is required.');
      return;
    }

    setSubmitting(true);
    try {
      let reqH = {};
      let reqB = null;
      let respH = {};
      let respB = null;

      try { reqH = JSON.parse(logForm.request_headers || '{}'); } catch { }
      try { reqB = JSON.parse(logForm.request_body || 'null'); } catch { }
      try { respH = JSON.parse(logForm.response_headers || '{}'); } catch { }
      try { respB = JSON.parse(logForm.response_body || 'null'); } catch { }

      await axios.post(`/projects/${activeProject.id}/logs`, {
        method: logForm.method,
        url: logForm.url,
        request_headers: reqH,
        request_body: reqB,
        response_headers: respH,
        response_body: respB,
        status_code: parseInt(logForm.status_code),
        response_time_ms: parseInt(logForm.response_time_ms),
      });

      setCreateModalOpen(false);
      // Reset form
      setLogForm({
        method: 'GET',
        url: '',
        request_headers: '{}',
        request_body: '{}',
        response_headers: '{}',
        response_body: '{}',
        status_code: 200,
        response_time_ms: 100,
      });
      fetchLogs();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.error?.message || 'Failed to create mock log payload.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!activeProject) {
    return (
      <div style={{ padding: '40px 0' }}>
        <EmptyState
          title="No Project Workspace"
          description="Create or select a project to start logging rest payloads."
          actionText="Projects"
          onActionClick={() => navigate('/projects')}
          icon="📁"
        />
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
            API Logs
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Inspect mock HTTP payloads and inspect automatically intercepted HTTP traffic.
          </p>
        </div>

        {activeTab === 'mock' && (
          <button className="btn btn-primary" onClick={() => setCreateModalOpen(true)}>
            + Create Log
          </button>
        )}
      </div>

      {/* Tabs Menu */}
      <div 
        style={{
          display: 'flex', borderBottom: '1px solid var(--border-color)',
          marginBottom: '24px', gap: '24px'
        }}
      >
        <button
          onClick={() => setActiveTab('mock')}
          style={{
            background: 'none', border: 'none', color: activeTab === 'mock' ? 'var(--color-primary)' : 'var(--text-secondary)',
            fontWeight: '600', fontSize: '0.95rem', paddingBottom: '12px', cursor: 'pointer',
            borderBottom: activeTab === 'mock' ? '2px solid var(--color-primary)' : '2px solid transparent',
            marginBottom: '-1px'
          }}
        >
          Mock API Logs ({logs.length})
        </button>
        <button
          onClick={() => setActiveTab('traffic')}
          style={{
            background: 'none', border: 'none', color: activeTab === 'traffic' ? 'var(--color-primary)' : 'var(--text-secondary)',
            fontWeight: '600', fontSize: '0.95rem', paddingBottom: '12px', cursor: 'pointer',
            borderBottom: activeTab === 'traffic' ? '2px solid var(--color-primary)' : '2px solid transparent',
            marginBottom: '-1px'
          }}
        >
          Captured HTTP Traffic ({traffic.length})
        </button>
      </div>

      {/* Search & Filters Controls */}
      <div 
        style={{
          display: 'flex', gap: '16px', flexWrap: 'wrap',
          marginBottom: '24px', alignItems: 'center'
        }}
      >
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', flex: 1, minWidth: '260px' }}>
          <input
            type="text"
            className="input-field"
            placeholder={activeTab === 'mock' ? "Search URL..." : "Search Path..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
          />
          <button 
            type="submit" 
            className="btn btn-secondary" 
            style={{ borderTopLeftRadius: 0, borderBottomLeftRadius: 0 }}
          >
            🔍 Search
          </button>
        </form>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select 
            className="select-field"
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
          >
            <option value="">All Methods</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
            <option value="PATCH">PATCH</option>
          </select>

          <select 
            className="select-field"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="200">200 OK</option>
            <option value="201">201 Created</option>
            <option value="204">204 No Content</option>
            <option value="400">400 Bad Request</option>
            <option value="401">401 Unauthorized</option>
            <option value="404">404 Not Found</option>
            <option value="422">422 Unprocessable</option>
            <option value="500">500 Server Error</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
          <div 
            style={{
              width: '32px', height: '32px', border: '3px solid var(--border-color)',
              borderTopColor: 'var(--color-primary)', borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}
          />
        </div>
      ) : (activeTab === 'mock' && logs.length === 0) || (activeTab === 'traffic' && traffic.length === 0) ? (
        <EmptyState
          title={activeTab === 'mock' ? "No Mock Logs Found" : "No Traffic Captured"}
          description={activeTab === 'mock' 
            ? "Create manual API requests with mock inputs and headers to test endpoints."
            : "Use your bearer authorization header when querying endpoints to record server traffic automatically."
          }
          icon="⚡"
        />
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th className="th" style={{ width: '100px' }}>Method</th>
                <th className="th">Endpoint / URL</th>
                <th className="th" style={{ width: '120px' }}>Status</th>
                <th className="th" style={{ width: '120px' }}>Latency</th>
                <th className="th" style={{ width: '200px' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {activeTab === 'mock' ? (
                logs.map((log) => (
                  <tr key={log.id} className="tr hover-row" onClick={() => openDetails(log)}>
                    <td className="td">
                      <span className={`badge badge-${log.method.toLowerCase()}`} style={{ width: '60px', justifyContent: 'center' }}>
                        {log.method}
                      </span>
                    </td>
                    <td className="td" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', wordBreak: 'break-all' }}>
                      {log.url}
                    </td>
                    <td className="td">
                      <span className={`badge ${log.status_code < 400 ? 'badge-success' : 'badge-danger'}`}>
                        {log.status_code}
                      </span>
                    </td>
                    <td className="td">{log.response_time_ms} ms</td>
                    <td className="td" style={{ color: 'var(--text-muted)' }}>
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                traffic.map((item) => (
                  <tr key={item.id} className="tr hover-row" onClick={() => openDetails(item)}>
                    <td className="td">
                      <span className={`badge badge-${item.method.toLowerCase()}`} style={{ width: '60px', justifyContent: 'center' }}>
                        {item.method}
                      </span>
                    </td>
                    <td className="td" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', wordBreak: 'break-all' }}>
                      {item.path}
                    </td>
                    <td className="td">
                      <span className={`badge ${item.response_status < 400 ? 'badge-success' : 'badge-danger'}`}>
                        {item.response_status}
                      </span>
                    </td>
                    <td className="td">{Math.round(item.response_time_ms)} ms</td>
                    <td className="td" style={{ color: 'var(--text-muted)' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Table Pagination */}
          <div className="pagination">
            <span className="pagination-info">Page {page} of {totalPages}</span>
            <div className="pagination-controls">
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setPage(p => Math.max(p - 1, 1))}
                disabled={page === 1}
              >
                ◀ Previous
              </button>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setPage(p => p + 1)}
                disabled={page >= totalPages}
              >
                Next ▶
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DETAILED LOG VIEWER DRAWER */}
      {drawerOpen && (
        <>
          <div className="drawer-overlay" onClick={closeDetails} />
          <div className={`drawer ${drawerOpen ? 'open' : ''}`}>
            <div className="drawer-header">
              <h3 className="drawer-title">Log Inspector</h3>
              <button className="modal-close" onClick={closeDetails}>&times;</button>
            </div>
            
            <div className="drawer-body">
              {/* Summary Stats Row */}
              <div 
                style={{
                  display: 'flex', gap: '16px', flexWrap: 'wrap',
                  padding: '16px', border: '1px solid var(--border-color)', borderRadius: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.005)'
                }}
              >
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Method</div>
                  <span className={`badge badge-${(selectedItem?.method || 'GET').toLowerCase()}`} style={{ marginTop: '4px' }}>
                    {selectedItem?.method}
                  </span>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Status</div>
                  <span 
                    className={`badge ${(selectedItem?.status_code || selectedItem?.response_status || 200) < 400 ? 'badge-success' : 'badge-danger'}`}
                    style={{ marginTop: '4px' }}
                  >
                    {selectedItem?.status_code || selectedItem?.response_status}
                  </span>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Response Time</div>
                  <span style={{ fontSize: '0.9rem', fontWeight: '600', display: 'inline-block', marginTop: '4px' }}>
                    {selectedItem?.response_time_ms || selectedItem?.response_time_ms} ms
                  </span>
                </div>
              </div>

              {/* Endpoint Path URL */}
              <div>
                <div className="section-title">Endpoint URL</div>
                <div 
                  style={{
                    fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-primary)',
                    padding: '10px 12px', border: '1px solid var(--border-color)', borderRadius: '6px',
                    backgroundColor: 'rgba(0,0,0,0.1)', wordBreak: 'break-all'
                  }}
                >
                  {selectedItem?.url || selectedItem?.path}
                </div>
              </div>

              {/* Drawer Tab Selectors */}
              <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', gap: '16px' }}>
                <button
                  onClick={() => setDrawerTab('request')}
                  style={{
                    background: 'none', border: 'none', color: drawerTab === 'request' ? 'var(--color-primary)' : 'var(--text-secondary)',
                    fontWeight: '600', fontSize: '0.85rem', paddingBottom: '8px', cursor: 'pointer',
                    borderBottom: drawerTab === 'request' ? '2px solid var(--color-primary)' : '2px solid transparent'
                  }}
                >
                  Request Payload
                </button>
                <button
                  onClick={() => setDrawerTab('response')}
                  style={{
                    background: 'none', border: 'none', color: drawerTab === 'response' ? 'var(--color-primary)' : 'var(--text-secondary)',
                    fontWeight: '600', fontSize: '0.85rem', paddingBottom: '8px', cursor: 'pointer',
                    borderBottom: drawerTab === 'response' ? '2px solid var(--color-primary)' : '2px solid transparent'
                  }}
                >
                  Response Payload
                </button>
              </div>

              {/* Drawer Details Content */}
              {drawerTab === 'request' ? (
                <>
                  <div>
                    <div className="section-title">Request Headers</div>
                    <pre className="code-panel">
                      {formatJSON(selectedItem?.request_headers)}
                    </pre>
                  </div>
                  <div>
                    <div className="section-title">Request Body</div>
                    <pre className="code-panel">
                      {selectedItem?.request_body ? formatJSON(selectedItem?.request_body) : '{ }'}
                    </pre>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <div className="section-title">Response Headers</div>
                    <pre className="code-panel">
                      {formatJSON(selectedItem?.response_headers)}
                    </pre>
                  </div>
                  <div>
                    <div className="section-title">Response Body</div>
                    <pre className="code-panel">
                      {selectedItem?.response_body ? formatJSON(selectedItem?.response_body) : '{ }'}
                    </pre>
                  </div>
                </>
              )}

              {/* Action Operations */}
              <div style={{ display: 'flex', gap: '12px', marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid var(--border-color)' }}>
                {activeTab === 'mock' ? (
                  <>
                    <button className="btn btn-primary" onClick={handleTriggerReplay} style={{ flex: 1 }}>
                      ⚡ Trigger Replay Request
                    </button>
                    <button className="btn btn-danger" onClick={handleDeleteLog}>
                      🗑️ Delete Log
                    </button>
                  </>
                ) : (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', width: '100%', textAlign: 'center' }}>
                    captured requests are read-only logs recorded directly from server transactions.
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* CREATE MOCK LOG MODAL */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Add Mock API Log"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateMockLog} disabled={submitting}>
              {submitting ? 'Creating...' : 'Save Log'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreateMockLog} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label className="input-label">HTTP Method</label>
              <select
                className="select-field"
                value={logForm.method}
                onChange={(e) => setLogForm({ ...logForm, method: e.target.value })}
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
              </select>
            </div>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label className="input-label">Status Code</label>
              <input
                type="number"
                className="input-field"
                value={logForm.status_code}
                onChange={(e) => setLogForm({ ...logForm, status_code: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Target URL Path</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. /api/v1/users"
              value={logForm.url}
              onChange={(e) => setLogForm({ ...logForm, url: e.target.value })}
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label className="input-label">Latency (ms)</label>
              <input
                type="number"
                className="input-field"
                value={logForm.response_time_ms}
                onChange={(e) => setLogForm({ ...logForm, response_time_ms: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Request Body (JSON string or empty)</label>
            <textarea
              className="input-field"
              style={{ minHeight: '60px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
              value={logForm.request_body}
              onChange={(e) => setLogForm({ ...logForm, request_body: e.target.value })}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Response Body (JSON string or empty)</label>
            <textarea
              className="input-field"
              style={{ minHeight: '60px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
              value={logForm.response_body}
              onChange={(e) => setLogForm({ ...logForm, response_body: e.target.value })}
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ApiLogs;
