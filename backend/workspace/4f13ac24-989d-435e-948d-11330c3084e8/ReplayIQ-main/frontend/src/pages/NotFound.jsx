import React from 'react';
import { useNavigate } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div 
      style={{
        minHeight: '80vh', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', textAlign: 'center',
        padding: '24px'
      }}
    >
      <div 
        style={{
          fontSize: '6rem', fontWeight: '800', color: 'rgba(255, 255, 255, 0.05)',
          lineHeight: '1', marginBottom: '16px', letterSpacing: '-0.05em'
        }}
      >
        404
      </div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '8px', letterSpacing: '-0.025em' }}>
        Page not found
      </h1>
      <p 
        style={{
          color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '380px',
          lineHeight: '1.6', marginBottom: '24px'
        }}
      >
        Sorry, we couldn't find the page you are looking for. It might have been moved or deleted.
      </p>
      <button className="btn btn-primary" onClick={() => navigate('/')}>
        Go Back Home
      </button>
    </div>
  );
};

export default NotFound;
