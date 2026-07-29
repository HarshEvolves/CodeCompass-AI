import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Register = () => {
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fullName.trim() || !email || !password) {
      setError('Please fill in all the required fields.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await register(email, password, fullName);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2500);
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error.message);
      } else {
        setError('Failed to register. Email may already be in use.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div 
            style={{
              width: '36px', height: '36px', backgroundColor: 'var(--color-primary)',
              borderRadius: '8px', display: 'flex', alignItems: 'center', justifycontent: 'center',
              fontWeight: '800', fontSize: '1.25rem', color: 'white', margin: '0 auto 16px',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}
          >
            R
          </div>
          <h2 className="auth-title">Create your account</h2>
          <p className="auth-subtitle">Get started with ReplayIQ today</p>
        </div>

        {success ? (
          <div 
            style={{
              backgroundColor: 'var(--color-success-dim)', border: '1px solid var(--color-success)',
              borderRadius: '6px', padding: '16px', fontSize: '0.875rem', color: 'var(--color-success)',
              textAlign: 'center', marginBottom: '20px'
            }}
          >
            🎉 Account created successfully! Redirecting you to login...
          </div>
        ) : (
          <>
            {error && (
              <div className="error-banner">
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="input-label" htmlFor="fullName">Full name</label>
                <input
                  id="fullName"
                  type="text"
                  className="input-field"
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="input-label" htmlFor="email">Email address</label>
                <input
                  id="email"
                  type="email"
                  className="input-field"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="input-label" htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  className="input-field"
                  placeholder="Min. 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button 
                type="submit" 
                className="btn btn-primary" 
                style={{ width: '100%', padding: '10px' }}
                disabled={submitting}
              >
                {submitting ? 'Creating account...' : 'Create account'}
              </button>
            </form>
          </>
        )}

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ fontWeight: '500' }}>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
