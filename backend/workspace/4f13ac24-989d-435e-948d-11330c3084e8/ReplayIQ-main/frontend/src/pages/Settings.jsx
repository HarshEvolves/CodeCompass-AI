import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Settings = () => {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handlePasswordUpdate = (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('Please fill in all the password fields.');
      return;
    }

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    setSubmitting(true);
    // Mocking update delay for visual excellence and transition feedback
    setTimeout(() => {
      setSuccess('🎉 Password updated successfully (Mock transaction).');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setSubmitting(false);
    }, 1000);
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
          Settings
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Manage your account profile, change security settings, and configure the application interface.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {/* Profile Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">User Profile</h3>
          </div>
          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="input-label">Full Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={user?.full_name || ''}
                  disabled
                  style={{ opacity: 0.8, cursor: 'not-allowed', backgroundColor: 'rgba(255, 255, 255, 0.01)' }}
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="input-label">Email Address</label>
                <input
                  type="email"
                  className="input-field"
                  value={user?.email || ''}
                  disabled
                  style={{ opacity: 0.8, cursor: 'not-allowed', backgroundColor: 'rgba(255, 255, 255, 0.01)' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Change Password Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Security & Password</h3>
          </div>
          <div className="card-body" style={{ maxWidth: '480px' }}>
            {error && (
              <div className="error-banner">
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div 
                style={{
                  backgroundColor: 'var(--color-success-dim)', border: '1px solid var(--color-success)',
                  borderRadius: '6px', padding: '12px', fontSize: '0.85rem', color: 'var(--color-success)',
                  marginBottom: '20px'
                }}
              >
                {success}
              </div>
            )}

            <form onSubmit={handlePasswordUpdate}>
              <div className="form-group">
                <label className="input-label" htmlFor="currentPass">Current Password</label>
                <input
                  id="currentPass"
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="input-label" htmlFor="newPass">New Password</label>
                <input
                  id="newPass"
                  type="password"
                  className="input-field"
                  placeholder="Min. 8 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="input-label" htmlFor="confirmPass">Confirm New Password</label>
                <input
                  id="confirmPass"
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        </div>

        {/* Interface Customization Theme Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Interface Settings</h3>
          </div>
          <div className="card-body">
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="input-label" style={{ marginBottom: '10px' }}>Active Application Theme</label>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button 
                  className="btn btn-secondary" 
                  disabled
                  style={{
                    borderColor: 'var(--color-primary)', color: 'var(--color-primary)',
                    backgroundColor: 'rgba(59, 130, 246, 0.05)', cursor: 'default', opacity: 1
                  }}
                >
                  🌌 Dark Theme (Active)
                </button>
                <button 
                  className="btn btn-secondary"
                  disabled
                  style={{ opacity: 0.5, cursor: 'not-allowed' }}
                >
                  ☀️ Light Theme (Disabled)
                </button>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '10px' }}>
                ReplayIQ operates on a dark theme optimized for developer comfort and visual data density.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
