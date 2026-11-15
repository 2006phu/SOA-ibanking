import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../common/Toast';
import { formatCurrency } from '../../utils/formatters';
import {
  EmvSmartChip,
  SyncIcon,
  EyeIcon,
  EyeOffIcon,
  CopyIcon,
  CheckIcon,
  ShieldCheckIcon,
  InfoIcon,
  GraduationCapIcon,
  ReceiptIcon,
  ArrowRightIcon,
} from '../common/Icons';
import './Dashboard.css';

const Dashboard = () => {
  const { user, refreshUser } = useAuth();
  const { success, info } = useToast();
  const navigate = useNavigate();
  const [showBalance, setShowBalance] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [copied, setCopied] = useState(false);

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
      setCopied(true);
      info('Đã sao chép mã tài khoản vào bộ nhớ tạm.');
      setTimeout(() => setCopied(false), 2000);
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
        {/* Fintech Virtual Card with Realistic EMV Chip */}
        <div className="fintech-card">
          <div className="fintech-card-bg-pattern"></div>

          <div className="card-top">
            <div className="card-chip-container">
              <EmvSmartChip />
              <span className="card-type-label">TDTU iCard • Platinum</span>
            </div>
            <button
              onClick={handleRefresh}
              className="btn-toggle-eye"
              title="Làm mới số dư thời gian thực"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <SyncIcon
                size={14}
                style={{
                  transform: isRefreshing ? 'rotate(360deg)' : 'none',
                  transition: 'transform 0.5s ease',
                }}
              />
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
                {showBalance ? (
                  <>
                    <EyeIcon size={14} /> <span>Ẩn</span>
                  </>
                ) : (
                  <>
                    <EyeOffIcon size={14} /> <span>Hiện</span>
                  </>
                )}
              </button>
            </div>
            <div className="balance-display-val">
              {showBalance ? formatCurrency(user.balance) : '•••••••• ₫'}
            </div>
          </div>

          <div className="card-bottom">
            <div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '2px', letterSpacing: '0.05em' }}>
                Chủ tài khoản
              </div>
              <div className="card-holder-name">{user.full_name}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '2px', letterSpacing: '0.05em' }}>
                Mã định danh
              </div>
              <div
                className="card-masked-number"
                onClick={handleCopyAccount}
                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', justifyContent: 'flex-end' }}
                title="Nhấn để sao chép"
              >
                <span>{user.id ? `${String(user.id).slice(0, 8)}...` : '5240 •••• 9999'}</span>
                {copied ? (
                  <CheckIcon size={14} style={{ color: '#34d399' }} />
                ) : (
                  <CopyIcon size={14} style={{ color: '#cbd5e1' }} />
                )}
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
              <span className="info-val" style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheckIcon size={16} />
                <span>2FA Email OTP (Gmail SMTP)</span>
              </span>
            </div>
          </div>

          <div style={{ background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: '10px', border: '1px solid #e2e8f0', marginTop: '1rem', display: 'flex', gap: '0.65rem', alignItems: 'flex-start' }}>
            <InfoIcon size={18} style={{ color: '#2563eb', flexShrink: 0, marginTop: '2px' }} />
            <p style={{ fontSize: '0.8rem', color: '#475569', lineHeight: 1.45, margin: 0 }}>
              <strong>Lưu ý:</strong> Khi thực hiện giao dịch thanh toán, mã OTP 6 số sẽ được gửi về hộp thư <strong>{user.email}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-main)', fontWeight: 700 }}>
          Dịch vụ trực tuyến
        </h2>
        <div className="dashboard-actions-grid">
          <div className="action-card" onClick={() => navigate('/payment')}>
            <div className="action-icon-wrapper icon-payment">
              <GraduationCapIcon size={26} />
            </div>
            <div className="action-text">
              <h3>Thanh toán học phí</h3>
              <p>Tra cứu công nợ sinh viên TDTU theo MSSV và nộp học phí qua mã OTP</p>
            </div>
            <div className="action-arrow">
              <ArrowRightIcon size={18} />
            </div>
          </div>

          <div className="action-card" onClick={() => navigate('/history')}>
            <div className="action-icon-wrapper icon-history">
              <ReceiptIcon size={26} />
            </div>
            <div className="action-text">
              <h3>Lịch sử giao dịch</h3>
              <p>Đối soát biên lai thu tiền điện tử và các khoản thanh toán đã hoàn tất</p>
            </div>
            <div className="action-arrow">
              <ArrowRightIcon size={18} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
