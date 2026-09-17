import React, { createContext, useState, useEffect, useContext } from 'react';
import axiosClient from '../api/axiosClient';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    if (token) {
      try {
        const userData = await axiosClient.get('/users/me');
        setUser(userData);
      } catch (error) {
        console.error("Failed to fetch user from /users/me, falling back to /auth/me:", error);
        try {
          const authData = await axiosClient.get('/auth/me');
          setUser(authData);
        } catch (authError) {
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUser();
  }, [token]);

  const refreshUser = async () => {
    if (token) {
      try {
        const userData = await axiosClient.get('/users/me');
        setUser(userData);
        return userData;
      } catch (error) {
        console.error("Failed to refresh user:", error);
      }
    }
  };

  const login = async (username, password) => {
    const response = await axiosClient.post('/auth/login', { username, password });
    const { access_token: token, user: userData } = response;
    localStorage.setItem('token', token);
    setToken(token);
    try {
      const liveUser = await axiosClient.get('/users/me');
      setUser(liveUser);
    } catch {
      setUser(userData);
    }
    return response;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    logout,
    refreshUser,
    isAuthenticated: !!token,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
