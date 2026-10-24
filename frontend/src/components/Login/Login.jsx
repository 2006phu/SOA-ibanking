import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../common/Toast';
import './Login.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const { success } = useToast();
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      success('Đăng nhập thành công! Chào mừng bạn trở lại.');
      navigate('/dashboard');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (u, p) => {
    setUsername(u);
    setPassword(p);
    setError('');
  };

  return (
    <div className="login-page">
      <div className="login-wrapper">
        <div className="login-card">
          <div className="login-header">
            <div className="login-brand-icon">🏛️</div>
            <h2>iBanking TDTU</h2>
            <p>Hệ thống thanh toán học phí trực tuyến</p>
          </div>

          {error && (
            <div className="login-error" role="alert">
              <span>⚠️</span>
              <div>{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="username" className="form-label">
                Tên đăng nhập
              </label>
              <input
                type="text"
                id="username"
                className="form-control"
                placeholder="Nhập username (ví dụ: student1)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Mật khẩu
              </label>
              <div className="input-with-icon">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className="form-control"
                  placeholder="Nhập mật khẩu"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="input-toggle-pwd"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? '👁️' : '🙈'}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary login-btn"
              disabled={isLoading || !username.trim() || !password}
            >
              {isLoading ? 'Đang xác thực...' : 'Đăng nhập vào hệ thống'}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="demo-accounts">
            <div className="demo-title">⚡ Tài khoản dùng thử nhanh (Demo)</div>
            <div className="demo-pills">
              <button
                type="button"
                className="demo-pill-btn"
                onClick={() => handleQuickFill('student1', 'password123')}
              >
                <div>student1</div>
                <span className="demo-balance">15.000.000 ₫</span>
              </button>
              <button
                type="button"
                className="demo-pill-btn"
                onClick={() => handleQuickFill('parent1', 'password123')}
              >
                <div>parent1</div>
                <span className="demo-balance">25.000.000 ₫</span>
              </button>
              <button
                type="button"
                className="demo-pill-btn"
                onClick={() => handleQuickFill('rich_user', 'password123')}
              >
                <div>rich_user</div>
                <span className="demo-balance">100.000.000 ₫</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
