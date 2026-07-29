import React, { useState } from 'react';
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const { user, projects, activeProject, setActiveProject, logout } = useAuth();
  const [showProjectDropdown, setShowProjectDropdown] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Define sidebar menu links
  const menuItems = [
    { name: 'Dashboard', path: '/', icon: '📊' },
    { name: 'Projects', path: '/projects', icon: '📁' },
    { name: 'API Logs', path: '/logs', icon: '📝' },
    { name: 'Replays', path: '/replays', icon: '🔄' },
    { name: 'Analytics', path: '/analytics', icon: '📈' },
    { name: 'Settings', path: '/settings', icon: '⚙️' },
  ];

  // Resolve current active menu item name for breadcrumbs
  const getActivePageName = () => {
    if (location.pathname === '/') return 'Dashboard';
    const activeItem = menuItems.find(item => item.path !== '/' && location.pathname.startsWith(item.path));
    return activeItem ? activeItem.name : 'View';
  };

  const handleProjectSelect = (project) => {
    setActiveProject(project);
    setShowProjectDropdown(false);
  };

  return (
    <div className="app-container">
      {/* Sidebar Overlay for Mobile */}
      {mobileSidebarOpen && (
        <div 
          style={{
            position: 'fixed',
            top: 0, bottom: 0, left: 0, right: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 95
          }}
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Left fixed Sidebar */}
      <aside className={`sidebar ${mobileSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-logo">
          <div className="logo-icon">R</div>
          <span>ReplayIQ</span>
        </div>

        <nav className="sidebar-menu">
          {menuItems.map((item) => {
            const isActive = item.path === '/' 
              ? location.pathname === '/' 
              : location.pathname.startsWith(item.path);

            return (
              <Link
                key={item.name}
                to={item.path}
                className={`sidebar-link ${isActive ? 'active' : ''}`}
                onClick={() => setMobileSidebarOpen(false)}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          {user && (
            <div className="user-profile-badge">
              <div className="user-avatar">
                {user.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="user-info">
                <span className="user-name">{user.full_name}</span>
                <span className="user-email">{user.email}</span>
              </div>
            </div>
          )}
          
          <button 
            className="btn btn-secondary btn-sm"
            onClick={logout}
            style={{ width: '100%', justifyContent: 'flex-start', gap: '10px' }}
          >
            🚪 Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Top navigation bar */}
        <header className="topbar">
          <div className="topbar-left">
            {/* Sidebar toggle button for mobile */}
            <button 
              className="btn btn-secondary btn-sm"
              style={{ display: 'none', padding: '6px 10px', fontSize: '1rem' }}
              className="mobile-toggle-btn"
              onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
            >
              ☰
            </button>
            <style>{`
              @media (max-width: 1024px) {
                .mobile-toggle-btn { display: inline-flex !important; }
              }
            `}</style>
            
            <div className="breadcrumbs">
              <span>ReplayIQ</span>
              <span className="breadcrumb-separator">/</span>
              <span className="breadcrumb-active">{getActivePageName()}</span>
            </div>
          </div>

          <div className="topbar-right">
            {/* Global Project Selector Dropdown */}
            {activeProject ? (
              <div className="project-selector-wrapper">
                <button 
                  className="project-selector-btn"
                  onClick={() => setShowProjectDropdown(!showProjectDropdown)}
                >
                  📁 {activeProject.name} ▾
                </button>
                {showProjectDropdown && (
                  <div className="project-selector-dropdown">
                    {projects.map((project) => (
                      <button
                        key={project.id}
                        className={`project-option ${project.id === activeProject.id ? 'active' : ''}`}
                        onClick={() => handleProjectSelect(project)}
                      >
                        {project.name}
                      </button>
                    ))}
                    <div className="project-selector-divider" />
                    <button
                      className="project-option"
                      style={{ color: 'var(--color-primary)', fontWeight: '500' }}
                      onClick={() => {
                        setShowProjectDropdown(false);
                        navigate('/projects');
                      }}
                    >
                      + Manage Projects
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => navigate('/projects')}
              >
                + Create First Project
              </button>
            )}
          </div>
        </header>

        {/* Scrollable page views container */}
        <main className="page-wrapper" onClick={() => setShowProjectDropdown(false)}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
