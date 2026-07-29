import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from '../services/axios';
import Modal from '../components/Modal';
import EmptyState from '../components/EmptyState';

const Projects = () => {
  const { projects, activeProject, setActiveProject, refreshProjects } = useAuth();
  
  // Modals visibility states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  // Form states
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const openCreateModal = () => {
    setProjectName('');
    setProjectDesc('');
    setError('');
    setCreateModalOpen(true);
  };

  const openEditModal = (project) => {
    setSelectedProject(project);
    setProjectName(project.name);
    setProjectDesc(project.description || '');
    setError('');
    setEditModalOpen(true);
  };

  const openDeleteModal = (project) => {
    setSelectedProject(project);
    setError('');
    setDeleteModalOpen(true);
  };

  // Trigger project creation
  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!projectName.trim()) {
      setError('Project name cannot be blank.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const res = await axios.post('/projects', {
        name: projectName,
        description: projectDesc || null,
      });
      // Refresh projects list and set the newly created project as active
      await refreshProjects(res.data.id);
      setCreateModalOpen(false);
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error.message);
      } else {
        setError('Failed to create project. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Trigger project update
  const handleEditProject = async (e) => {
    e.preventDefault();
    if (!projectName.trim()) {
      setError('Project name cannot be blank.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await axios.put(`/projects/${selectedProject.id}`, {
        name: projectName,
        description: projectDesc || null,
      });
      await refreshProjects();
      setEditModalOpen(false);
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error.message);
      } else {
        setError('Failed to update project. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Trigger project deletion
  const handleDeleteProject = async () => {
    setSubmitting(true);
    setError('');

    try {
      await axios.delete(`/projects/${selectedProject.id}`);
      // Refresh list: if we deleted the current active project, it will fall back to another one
      await refreshProjects();
      setDeleteModalOpen(false);
    } catch (err) {
      console.error(err);
      setError('Failed to delete project. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div 
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: '32px'
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.03em', marginBottom: '8px' }}>
            Projects
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Manage your project workspaces and select the active workspace.
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreateModal}>
          + Create Project
        </button>
      </div>

      {projects.length === 0 ? (
        <EmptyState
          title="No Projects Available"
          description="Create your first project workspace to start capturing REST request logs, triggering test replays, and running comparisons."
          actionText="Create Project"
          onActionClick={openCreateModal}
          icon="📁"
        />
      ) : (
        <div 
          style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '24px'
          }}
        >
          {projects.map((project) => {
            const isActive = activeProject && activeProject.id === project.id;
            
            return (
              <div 
                key={project.id} 
                className={`card ${isActive ? '' : 'hover-lift'}`}
                style={{
                  display: 'flex', flexDirection: 'column', height: '100%',
                  borderColor: isActive ? 'var(--color-primary)' : 'var(--border-color)',
                  boxShadow: isActive ? '0 0 0 1px var(--color-primary)' : 'none'
                }}
              >
                <div className="card-header" style={{ borderBottom: 'none', paddingBottom: '10px' }}>
                  <h3 className="card-title" style={{ fontSize: '1.1rem', wordBreak: 'break-all' }}>
                    {project.name}
                  </h3>
                  {isActive && (
                    <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                      Active
                    </span>
                  )}
                </div>

                <div className="card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', paddingTop: '10px' }}>
                  <p 
                    style={{
                      color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '24px',
                      wordBreak: 'break-word', minHeight: '40px'
                    }}
                  >
                    {project.description || 'No description provided.'}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button 
                        className="btn btn-secondary btn-sm"
                        onClick={() => openEditModal(project)}
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        className="btn btn-secondary btn-sm"
                        style={{ color: 'var(--color-danger)' }}
                        onClick={() => openDeleteModal(project)}
                      >
                        🗑️ Delete
                      </button>
                    </div>

                    {!isActive && (
                      <button 
                        className="btn btn-primary btn-sm"
                        onClick={() => setActiveProject(project)}
                      >
                        Select
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* CREATE PROJECT MODAL */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create New Project"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateProject} disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Project'}
            </button>
          </>
        }
      >
        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}
        <form onSubmit={handleCreateProject}>
          <div className="form-group">
            <label className="input-label">Project Name</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Payments API v1"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              required
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Description (Optional)</label>
            <textarea
              className="input-field"
              style={{ minHeight: '80px', resize: 'vertical' }}
              placeholder="What is this project workspace for?"
              value={projectDesc}
              onChange={(e) => setProjectDesc(e.target.value)}
            />
          </div>
        </form>
      </Modal>

      {/* EDIT PROJECT MODAL */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Project Workspace"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setEditModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleEditProject} disabled={submitting}>
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </>
        }
      >
        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}
        <form onSubmit={handleEditProject}>
          <div className="form-group">
            <label className="input-label">Project Name</label>
            <input
              type="text"
              className="input-field"
              placeholder="Project Name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              required
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Description (Optional)</label>
            <textarea
              className="input-field"
              style={{ minHeight: '80px', resize: 'vertical' }}
              placeholder="Description"
              value={projectDesc}
              onChange={(e) => setProjectDesc(e.target.value)}
            />
          </div>
        </form>
      </Modal>

      {/* DELETE PROJECT CONFIRMATION MODAL */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Project Workspace"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-danger" onClick={handleDeleteProject} disabled={submitting}>
              {submitting ? 'Deleting...' : 'Delete Project'}
            </button>
          </>
        }
      >
        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}
        <div style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-secondary)' }}>
          <p style={{ marginBottom: '12px' }}>
            Are you sure you want to delete <strong style={{ color: 'var(--text-primary)' }}>{selectedProject?.name}</strong>?
          </p>
          <p style={{ color: 'var(--color-danger)', fontWeight: '500' }}>
            ⚠️ This action is irreversible. All stored REST logs and replay data for this project will be permanently erased.
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default Projects;
