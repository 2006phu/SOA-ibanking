import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { formatCurrency } from '../../utils/formatters';
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

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    return parts[parts.length - 1].charAt(0).toUpperCase();
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Brand */}
        <Link to="/dashboard" className="navbar-brand">
          <div className="brand-icon">iB</div>
          <div className="brand-info">
            <div className="brand-title">
              iBanking <span className="brand-badge">TDTU</span>
            </div>
            <span className="brand-subtitle">Cổng Học Phí Trực Tuyến</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <div className="navbar-menu">
          <Link
            to="/dashboard"
            className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
          >
            <span>🏠</span>
            <span>Tổng quan</span>
          </Link>
          <Link
            to="/payment"
            className={`nav-link ${location.pathname === '/payment' ? 'active' : ''}`}
          >
            <span>💳</span>
            <span>Nộp học phí</span>
          </Link>
          <Link
            to="/history"
            className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}
          >
            <span>📜</span>
            <span>Lịch sử</span>
          </Link>
        </div>

        {/* User Pill & Logout */}
        <div className="navbar-user">
          {user?.balance !== undefined && (
            <div className="user-balance-pill">
              <span className="user-balance-label">Số dư khả dụng</span>
              <span className="user-balance-val">{formatCurrency(user.balance)}</span>
            </div>
          )}

          <div className="user-profile-badge">
            <div className="avatar-circle" title={user?.full_name || 'Người dùng'}>
              {getInitials(user?.full_name)}
            </div>
            <button
              onClick={handleLogout}
              className="btn-logout"
              title="Đăng xuất khỏi hệ thống"
            >
              Đăng xuất
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
