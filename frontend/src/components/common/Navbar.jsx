import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!isAuthenticated) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/dashboard">iBanking TDTU</Link>
        </div>
        <div className="navbar-menu">
          <Link to="/dashboard" className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}>
            Trang chủ
          </Link>
          <Link to="/payment" className={`nav-link ${location.pathname === '/payment' ? 'active' : ''}`}>
            Thanh toán học phí
          </Link>
          <Link to="/history" className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}>
            Lịch sử
          </Link>
        </div>
        <div className="navbar-user">
          <span className="user-name">Xin chào, {user?.full_name || 'Khách'}</span>
          <button onClick={handleLogout} className="btn-logout">
            Đăng xuất
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
