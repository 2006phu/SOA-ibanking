import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { formatCurrency } from '../../utils/formatters';
import './Dashboard.css';

const Dashboard = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (refreshUser) {
      refreshUser();
    }
  }, []);

  if (!user) return null;

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Tổng quan tài khoản</h1>
      </div>

      <div className="card account-card">
        <div className="account-balance">
          <h3>Số dư khả dụng</h3>
          <div className="balance-amount">{formatCurrency(user.balance)}</div>
        </div>
        
        <div className="account-details">
          <div className="detail-item">
            <span className="detail-label">Họ và tên:</span>
            <span className="detail-value">{user.full_name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Email:</span>
            <span className="detail-value">{user.email}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Số điện thoại:</span>
            <span className="detail-value">{user.phone}</span>
          </div>
        </div>
      </div>

      <div className="dashboard-actions">
        <div className="action-card" onClick={() => navigate('/payment')}>
          <div className="action-icon payment-icon">💸</div>
          <h3>Thanh toán học phí</h3>
          <p>Tra cứu và thanh toán học phí sinh viên</p>
        </div>
        
        <div className="action-card" onClick={() => navigate('/history')}>
          <div className="action-icon history-icon">📋</div>
          <h3>Lịch sử giao dịch</h3>
          <p>Xem lại các giao dịch đã thực hiện</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
