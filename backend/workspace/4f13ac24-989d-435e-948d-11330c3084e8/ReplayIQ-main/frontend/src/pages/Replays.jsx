import React, { useState, useEffect } from 'react';
import { useLocation, useSearchParams, useNavigate } from 'react-router-dom';
import axios from '../services/axios';
import EmptyState from '../components/EmptyState';

const Replays = () => {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const projectId = searchParams.get('project_id');
  const logId = searchParams.get('log_id');
  const replayId = searchParams.get('replay_id');

  // Load from navigation state if navigated directly after triggering replay
  const stateOriginalLog = location.state?.originalLog;
  const stateReplayResult = location.state?.replayResult;

  const [originalLog, setOriginalLog] = useState(stateOriginalLog || null);
  const [replayResult, setReplayResult] = useState(stateReplayResult || null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load comparison data from backend using the query params
  const fetchComparisonData = async () => {
    if (!projectId || !logId || !replayId) return;

    setLoading(true);
    setError('');
    try {
      // Fetch comparison summary details
      const compRes = await axios.get(
        `/projects/${projectId}/logs/${logId}/replays/${replayId}/comparison`
      );
      setComparison(compRes.data);

      // If we didn't get original log details from state, fetch them
      if (!originalLog) {
        const logRes = await axios.get(`/projects/${projectId}/logs/${logId}`);
        setOriginalLog(logRes.data);
      }
    } catch (err) {
      console.error('Failed to load comparison', err);
      setError('Could not retrieve comparison details. Ensure backend service is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparisonData();
  }, [projectId, logId, replayId]);

  if (!projectId || !logId || !replayId) {
    return (
      <div style={{ padding: '40px 0' }}>
        <EmptyState
          title="No Replay Inspected"
          description="Go to the API Logs tab, select a mock API log payload, and click 'Trigger Replay' to run a REST transaction regression check."
          actionText="Go to API Logs"
          onActionClick={() => navigate('/logs')}
          icon="🔄"
        />
      </div>
    );
  }

  if (loading && !comparison) {
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

  // Render a clean visual code diff highlighting changes in JSON bodies
  const renderJSONDiff = () => {
    const parseBody = (body) => {
      if (!body) return {};
      if (typeof body === 'object') return body;
      try { return JSON.parse(body); } catch { return {}; }
    };

    const origObj = originalLog ? parseBody(originalLog.response_body) : {};
    
    // Attempt to load replayed body from direct result state or fallback empty
    const replObj = replayResult ? parseBody(replayResult.replay_response_body) : null;

    if (!replObj) {
      // Fallback if full replayed body is not in state (e.g. page refreshed)
      // Display the keys according to body comparison fields
      const bodyComp = comparison?.body;
      if (!bodyComp) return <div style={{ color: 'var(--text-muted)' }}>No comparison detail available.</div>;

      return (
        <div className="diff-container">
          <div style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>
            ℹ️ Detail view is only available immediately after triggering replay. Fallback keys diff:
          </div>
          {bodyComp.added_fields.map(field => (
            <div key={field} className="diff-line diff-added">+ "{field}": [Added Field in Replay]</div>
          ))}
          {bodyComp.removed_fields.map(field => (
            <div key={field} className="diff-line diff-removed">- "{field}": "{origObj[field] != null ? origObj[field] : ''}"</div>
          ))}
          {bodyComp.modified_fields.map(field => (
            <div key={field} className="diff-line diff-modified">~ "{field}": "{origObj[field] != null ? origObj[field] : ''}" ➜ [Modified Value]</div>
          ))}
          {!bodyComp.body_changed && (
            <div style={{ color: 'var(--color-success)' }}>🟢 Response bodies match perfectly.</div>
          )}
        </div>
      );
    }

    // Full side-by-side recursive visual comparison
    const allKeys = Array.from(new Set([...Object.keys(origObj), ...Object.keys(replObj)])).sort();
    
    return (
      <div className="diff-container">
        {allKeys.map((key) => {
          const inOrig = key in origObj;
          const inRepl = key in replObj;
          const valOrig = origObj[key];
          const valRepl = replObj[key];

          const isModified = inOrig && inRepl && JSON.stringify(valOrig) !== JSON.stringify(valRepl);

          if (isModified) {
            return (
              <React.Fragment key={key}>
                <div className="diff-line diff-removed">
                  - "{key}": {JSON.stringify(valOrig)}
                </div>
                <div className="diff-line diff-added">
                  + "{key}": {JSON.stringify(valRepl)}
                </div>
              </React.Fragment>
            );
          } else if (inOrig && !inRepl) {
            return (
              <div key={key} className="diff-line diff-removed">
                - "{key}": {JSON.stringify(valOrig)}
              </div>
            );
          } else if (!inOrig && inRepl) {
            return (
              <div key={key} className="diff-line diff-added">
                + "{key}": {JSON.stringify(valRepl)}
              </div>
            );
          } else {
            return (
              <div key={key} className="diff-line" style={{ color: 'var(--text-secondary)' }}>
                &nbsp;&nbsp; "{key}": {JSON.stringify(valOrig)}
              </div>
            );
          }
        })}
        {allKeys.length === 0 && <div style={{ color: 'var(--text-muted)' }}>&#123; &#125; (Empty JSON Body)</div>}
      </div>
    );
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
            Replay Comparison
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Check regressions by comparing the original transaction with the replayed REST request response.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate('/logs')}>
          Back to Logs
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Comparison Summary Overview Panel */}
      {comparison && (
        <div 
          className="card" 
          style={{
            borderColor: comparison.overall_changed ? 'var(--color-warning)' : 'var(--color-success)',
            marginBottom: '32px', padding: '24px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Regression Status</span>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '700', marginTop: '4px', color: comparison.overall_changed ? 'var(--color-warning)' : 'var(--color-success)' }}>
                {comparison.overall_changed ? '⚠️ Changes Detected' : '✅ No Changes (Passed)'}
              </h2>
            </div>
            
            <div style={{ display: 'flex', gap: '24px' }}>
              <div>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Status Check</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                  <span className={`badge ${comparison.status.status_changed ? 'badge-danger' : 'badge-success'}`}>
                    {comparison.status.status_changed ? 'Mismatch' : 'Match'}
                  </span>
                  <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>
                    {comparison.status.old_status} ➜ {comparison.status.new_status}
                  </span>
                </div>
              </div>

              <div>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Body Check</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                  <span className={`badge ${comparison.body.body_changed ? 'badge-danger' : 'badge-success'}`}>
                    {comparison.body.body_changed ? 'Changed' : 'Identical'}
                  </span>
                </div>
              </div>

              <div>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Latency Diff</span>
                <div style={{ fontSize: '0.9rem', fontWeight: '600', marginTop: '4px' }}>
                  {comparison.response_time.latency_difference_ms > 0 
                    ? `+${comparison.response_time.latency_difference_ms}ms slower`
                    : `${comparison.response_time.latency_difference_ms}ms faster`
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Payload Inspection Columns */}
      <div className="comparison-grid">
        {/* Original Request Details */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">1. Original REST Transaction</h3>
            <span className="badge badge-success">
              Status: {originalLog?.status_code}
            </span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Method / URL</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: '600' }}>
                {originalLog?.method} {originalLog?.url}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Latency</span>
              <span>{originalLog?.response_time_ms} ms</span>
            </div>
            
            <div>
              <div className="section-title">Response Headers</div>
              <pre className="code-panel" style={{ maxHeight: '180px' }}>
                {originalLog ? JSON.stringify(originalLog.response_headers, null, 2) : '{}'}
              </pre>
            </div>

            <div>
              <div className="section-title">Response Body</div>
              <pre className="code-panel" style={{ maxHeight: '240px' }}>
                {originalLog ? JSON.stringify(originalLog.response_body, null, 2) : '{}'}
              </pre>
            </div>
          </div>
        </div>

        {/* Replay Request Details */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">2. Replay Transaction</h3>
            <span className={`badge ${comparison?.status.status_changed ? 'badge-danger' : 'badge-success'}`}>
              Status: {replayResult ? replayResult.replay_status_code : (comparison?.status.new_status || 'Waiting')}
            </span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Status Success</span>
              <span style={{ fontWeight: '600', color: replayResult?.replay_success ? 'var(--color-success)' : 'inherit' }}>
                {replayResult ? (replayResult.replay_success ? 'Success' : 'Failed') : 'Completed'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Latency</span>
              <span>{replayResult ? replayResult.replay_response_time_ms : (comparison?.response_time.new_response_time_ms || 0)} ms</span>
            </div>

            <div>
              <div className="section-title">Response Headers</div>
              <pre className="code-panel" style={{ maxHeight: '180px' }}>
                {replayResult 
                  ? JSON.stringify(replayResult.replay_response_headers, null, 2)
                  : '{}'
                }
              </pre>
            </div>

            <div>
              <div className="section-title">Response Body</div>
              <pre className="code-panel" style={{ maxHeight: '240px' }}>
                {replayResult 
                  ? JSON.stringify(replayResult.replay_response_body, null, 2)
                  : '{}'
                }
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* Visual diff section */}
      <div style={{ marginTop: '32px' }}>
        <h3 className="section-title" style={{ marginBottom: '12px' }}>JSON Body Diff highlights</h3>
        {renderJSONDiff()}
      </div>
    </div>
  );
};

export default Replays;
