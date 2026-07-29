import React from 'react';

const EmptyState = ({ title, description, actionText, onActionClick, icon = '📁' }) => {
  return (
    <div className="empty-state">
      <div style={{ fontSize: '3rem', marginBottom: '8px' }}>{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-description">{description}</p>
      {actionText && onActionClick && (
        <button className="btn btn-primary" onClick={onActionClick} style={{ marginTop: '8px' }}>
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
