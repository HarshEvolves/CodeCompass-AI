import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from '../services/axios';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [loading, setLoading] = useState(true);

  // Helper to fetch user's projects from backend
  const fetchProjects = async () => {
    try {
      const response = await axios.get('/projects');
      const projectList = response.data;
      setProjects(projectList);

      if (projectList.length > 0) {
        // Retrieve last selected project ID from local storage
        const savedProjectId = localStorage.getItem('activeProjectId');
        const foundProject = projectList.find(p => p.id === savedProjectId);
        
        if (foundProject) {
          setActiveProject(foundProject);
        } else {
          setActiveProject(projectList[0]);
          localStorage.setItem('activeProjectId', projectList[0].id);
        }
      } else {
        setActiveProject(null);
        localStorage.removeItem('activeProjectId');
      }
    } catch (err) {
      console.error('Failed to fetch projects', err);
    }
  };

  // Helper to fetch user profile and initialize projects
  const fetchProfile = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
      await fetchProjects();
    } catch (err) {
      console.error('Failed to fetch user profile', err);
      // Check if it is a 400 validation error indicating that no projects exist yet
      const errorMsg = err.response?.data?.error?.message || '';
      if (err.response?.status === 400 && errorMsg.includes('No project exists')) {
        // Decode token to extract email as a placeholder
        let decodedEmail = 'User';
        try {
          const payload = token.split('.')[1];
          const decoded = JSON.parse(atob(payload));
          if (decoded && decoded.sub) {
            decodedEmail = decoded.sub;
          }
        } catch (e) {}
        
        setUser({ email: decodedEmail, full_name: 'Developer' });
        setProjects([]);
        setActiveProject(null);
      } else {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  // Handle user login
  const login = async (email, password) => {
    const data = await authService.login(email, password);
    const { access_token } = data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setLoading(true); // Triggers profile reload via useEffect
  };

  // Handle user registration
  const register = async (email, password, fullName) => {
    await authService.register(email, password, fullName);
  };

  // Handle logout
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('activeProjectId');
    setToken(null);
    setUser(null);
    setProjects([]);
    setActiveProject(null);
  };

  // Helper to change the active project globally
  const selectActiveProject = (project) => {
    if (project) {
      setActiveProject(project);
      localStorage.setItem('activeProjectId', project.id);
    } else {
      setActiveProject(null);
      localStorage.removeItem('activeProjectId');
    }
  };

  // Helper to refresh projects (e.g. after create/delete project)
  const refreshProjects = async (newActiveId = null) => {
    try {
      const response = await axios.get('/projects');
      const projectList = response.data;
      setProjects(projectList);

      if (projectList.length > 0) {
        // If a specific ID is provided or if the current active project is gone
        const targetId = newActiveId || (activeProject ? activeProject.id : null);
        const foundProject = projectList.find(p => p.id === targetId) || projectList[0];
        setActiveProject(foundProject);
        localStorage.setItem('activeProjectId', foundProject.id);

        // Re-fetch user profile since they now have a project and /users/me will succeed!
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (e) {
          console.error('Failed to load profile details after project creation', e);
        }
      } else {
        setActiveProject(null);
        localStorage.removeItem('activeProjectId');
      }
    } catch (err) {
      console.error('Failed to refresh projects', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        projects,
        activeProject,
        loading,
        login,
        register,
        logout,
        setActiveProject: selectActiveProject,
        refreshProjects,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
