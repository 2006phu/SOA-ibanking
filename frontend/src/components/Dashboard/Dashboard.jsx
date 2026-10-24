import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../common/Toast';
import { formatCurrency } from '../../utils/formatters';
import './Dashboard.css';

const Dashboard = () => {
  const { user, refreshUser } = useAuth();
  const { success, info } = useToast();
  const navigate = useNavigate();
  const [showBalance, setShowBalance] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (refreshUser) {
      refreshUser();
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      if (refreshUser) {
        await refreshUser();
        success('Số dư tài khoản đã được đồng bộ mới nhất!');
      }
    } catch (e) {
      // Handled
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  const handleCopyAccount = () => {
    if (user?.id) {
      navigator.clipboard?.writeText(user.id);
      info('Đã sao chép mã tài khoản vào bộ nhớ tạm.');
    }
  };

  if (!user) return null;

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-title-area">
          <h1>Tổng quan tài khoản</h1>
          <p className="dashboard-subtitle">
            Quản lý tài khoản thanh toán và dịch vụ tài chính học vụ TDTU
          </p>
        </div>
        <div className="system-status-chip">
          <span className="status-dot-pulse"></span>
          <span>Gateway & Microservices: Hoạt động ổn định</span>
        </div>
      </div>

      {/* Main Grid: Bank Card & User Details */}
      <div className="dashboard-grid">
        {/* Fintech Virtual Card */}
        <div className="fintech-card">
          <div className="fintech-card-bg-pattern"></div>

          <div className="card-top">
            <div className="card-chip-container">
              <div className="emv-chip"></div>
              <span className="card-type-label">TDTU iCard • Platinum</span>
            </div>
            <button
              onClick={handleRefresh}
              className="btn-toggle-eye"
              title="Làm mới số dư thời gian thực"
              style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <span style={{ display: 'inline-block', transform: isRefreshing ? 'rotate(360deg)' : 'none', transition: 'transform 0.5s' }}>
                🔄
              </span>
              <span>Đồng bộ</span>
            </button>
          </div>

          <div className="card-balance-section">
            <div className="balance-title-row">
              <span>Số dư khả dụng</span>
              <button
                type="button"
                className="btn-toggle-eye"
                onClick={() => setShowBalance(!showBalance)}
                aria-label={showBalance ? 'Ẩn số dư' : 'Hiện số dư'}
              >
                {showBalance ? '👁️ Ẩn' : '🙈 Hiện'}
              </button>
            </div>
            <div className="balance-display-val">
              {showBalance ? formatCurrency(user.balance) : '•••••••• ₫'}
            </div>
          </div>

          <div className="card-bottom">
            <div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '2px' }}>
                Chủ tài khoản
              </div>
              <div className="card-holder-name">{user.full_name}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '2px' }}>
                Mã định danh
              </div>
              <div className="card-masked-number" onClick={handleCopyAccount} style={{ cursor: 'pointer' }} title="Nhấn để sao chép">
                {user.id ? `${String(user.id).slice(0, 8)}...` : '5240 •••• 9999'} 📋
              </div>
            </div>
          </div>
        </div>

        {/* Profile Details Card */}
        <div className="card user-info-card">
          <div>
            <div className="user-info-card-header">
              <h3>Thông tin người dùng</h3>
              <span className="badge badge-success">
                <span className="badge-dot"></span> Đã xác thực
              </span>
            </div>

            <div className="info-item-row">
              <span className="info-label">Họ và tên</span>
              <span className="info-val">{user.full_name}</span>
            </div>
            <div className="info-item-row">
              <span className="info-label">Email thông báo</span>
              <span className="info-val text-mono">{user.email}</span>
            </div>
            <div className="info-item-row">
              <span className="info-label">Số điện thoại</span>
              <span className="info-val text-mono">{user.phone || '0901 234 567'}</span>
            </div>
            <div className="info-item-row">
              <span className="info-label">Phương thức bảo mật</span>
              <span className="info-val" style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '4px' }}>
                🛡️ 2FA Email OTP (Gmail SMTP)
              </span>
            </div>
          </div>

          <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginTop: '1rem' }}>
            <p style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.4 }}>
              💡 <strong>Lưu ý:</strong> Khi thực hiện giao dịch thanh toán, mã OTP 6 số sẽ được gửi về hộp thư <strong>{user.email}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-main)' }}>
          Dịch vụ trực tuyến
        </h2>
        <div className="dashboard-actions-grid">
          <div className="action-card" onClick={() => navigate('/payment')}>
            <div className="action-icon-wrapper icon-payment">
              🎓
            </div>
            <div className="action-text">
              <h3>Thanh toán học phí</h3>
              <p>Tra cứu công nợ sinh viên TDTU theo MSSV và nộp học phí qua mã OTP</p>
            </div>
            <div className="action-arrow">→</div>
          </div>

          <div className="action-card" onClick={() => navigate('/history')}>
            <div className="action-icon-wrapper icon-history">
              📜
            </div>
            <div className="action-text">
              <h3>Lịch sử giao dịch</h3>
              <p>Đối soát biên lai thu tiền điện tử và các khoản thanh toán đã hoàn tất</p>
            </div>
            <div className="action-arrow">→</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
