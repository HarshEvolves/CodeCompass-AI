import axios from './axios';

export const authService = {
  // Login with URL-encoded form data (as required by OAuth2PasswordRequestForm in FastAPI)
  login: async (email, password) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const response = await axios.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data; // Should return { access_token, token_type }
  },

  // Register a new user
  register: async (email, password, fullName) => {
    const response = await axios.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  // Get current logged in user details
  getCurrentUser: async () => {
    const response = await axios.get('/users/me');
    return response.data;
  },
};
