import React, { useState, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../common/Toast';
import {
  BankLogoIcon,
  AlertCircleIcon,
  EyeIcon,
  EyeOffIcon,
  BoltIcon,
  ArrowRightIcon,
} from '../common/Icons';
import './Login.css';

gsap.registerPlugin(useGSAP);

const DEMO_ACCOUNTS = [
  { username: 'lephu', password: '235780', label: 'lephu', badge: 'Chính', balance: '80.000.000 ₫', primary: true },
  { username: 'student1', password: 'password123', label: 'student1', badge: 'SV', balance: '15.000.000 ₫' },
  { username: 'parent1', password: 'password123', label: 'parent1', badge: 'PH', balance: '25.000.000 ₫' },
  { username: 'rich_user', password: 'password123', label: 'rich_user', badge: 'VIP', balance: '100.000.000 ₫' },
];

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const { success } = useToast();
  const navigate = useNavigate();

  const containerRef = useRef(null);
  const cardRef = useRef(null);
  const brandIconRef = useRef(null);
  const errorRef = useRef(null);
  const submitBtnRef = useRef(null);

  // GSAP Entrance and Ambient Animations
  useGSAP(() => {
    // Ambient floating glow orbs
    gsap.to('.ambient-orb-1', {
      x: 35,
      y: -25,
      duration: 8,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut',
    });

    gsap.to('.ambient-orb-2', {
      x: -30,
      y: 30,
      duration: 9,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut',
    });

    // Main entrance timeline with explicit fromTo and clearProps to guarantee full visibility
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.fromTo(
      cardRef.current,
      { y: 35, opacity: 0, scale: 0.96 },
      { y: 0, opacity: 1, scale: 1, duration: 0.7, clearProps: 'transform' }
    )
      .fromTo(
        brandIconRef.current,
        { scale: 0.4, opacity: 0, rotation: -12 },
        { scale: 1, opacity: 1, rotation: 0, duration: 0.5, ease: 'back.out(2)' },
        '-=0.35'
      )
      .fromTo(
        '.gsap-anim-item',
        { y: 14, opacity: 0 },
        { y: 0, opacity: 1, stagger: 0.05, duration: 0.4, clearProps: 'opacity,transform' },
        '-=0.25'
      );
  }, { scope: containerRef });

  // GSAP Error Shake effect
  useGSAP(() => {
    if (error && cardRef.current) {
      gsap.timeline()
        .to(cardRef.current, { x: -10, duration: 0.05, ease: 'power1.inOut' })
        .to(cardRef.current, { x: 10, duration: 0.05, ease: 'power1.inOut' })
        .to(cardRef.current, { x: -7, duration: 0.05, ease: 'power1.inOut' })
        .to(cardRef.current, { x: 7, duration: 0.05, ease: 'power1.inOut' })
        .to(cardRef.current, { x: -3, duration: 0.05, ease: 'power1.inOut' })
        .to(cardRef.current, { x: 0, duration: 0.05, ease: 'power1.inOut' });

      if (errorRef.current) {
        gsap.fromTo(
          errorRef.current,
          { opacity: 0, y: -8 },
          { opacity: 1, y: 0, duration: 0.3, ease: 'back.out(1.5)' }
        );
      }
    }
  }, { dependencies: [error], scope: containerRef });

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.');
      return;
    }

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

  const handleQuickFill = (acc, event) => {
    setUsername(acc.username);
    setPassword(acc.password);
    setError('');

    // GSAP micro-interaction bounce
    if (event && event.currentTarget) {
      gsap.timeline()
        .to(event.currentTarget, { scale: 0.92, duration: 0.08, ease: 'power1.out' })
        .to(event.currentTarget, { scale: 1, duration: 0.22, ease: 'back.out(2)' });
    }

    // Input highlight effect
    gsap.fromTo(
      '.login-input',
      { borderColor: '#3b82f6', backgroundColor: '#eff6ff' },
      { borderColor: '#e2e8f0', backgroundColor: '#f8fafc', duration: 0.5, ease: 'power2.out' }
    );
  };

  return (
    <div className="login-fullscreen-page" ref={containerRef}>
      {/* Dynamic Background Ambient Orbs & Grid */}
      <div className="ambient-orb ambient-orb-1" />
      <div className="ambient-orb ambient-orb-2" />
      <div className="ambient-grid-overlay" />

      <div className="login-wrapper">
        <div className="login-card" ref={cardRef}>
          {/* Header */}
          <div className="login-header">
            <div className="login-brand-icon" ref={brandIconRef}>
              <BankLogoIcon size={26} style={{ color: '#ffffff' }} />
              <div className="brand-glow" />
            </div>
            <h2 className="login-title gsap-anim-item">iBanking TDTU</h2>
            <p className="login-subtitle gsap-anim-item">Cổng thanh toán học phí trực tuyến hiện đại</p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="login-error-banner" ref={errorRef} role="alert">
              <AlertCircleIcon size={18} className="error-icon" />
              <div className="error-text">{error}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group gsap-anim-item">
              <label htmlFor="username" className="form-label">
                Tên đăng nhập
              </label>
              <input
                type="text"
                id="username"
                className="form-control login-input"
                placeholder="Nhập tên đăng nhập (ví dụ: lephu)"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  if (error) setError('');
                }}
                required
                autoFocus
              />
            </div>

            <div className="form-group gsap-anim-item">
              <label htmlFor="password" className="form-label">
                Mật khẩu
              </label>
              <div className="input-with-icon">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className="form-control login-input"
                  placeholder="Nhập mật khẩu"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError('');
                  }}
                  required
                />
                <button
                  type="button"
                  className="input-toggle-pwd"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  tabIndex="-1"
                >
                  {showPassword ? <EyeOffIcon size={18} /> : <EyeIcon size={18} />}
                </button>
              </div>
            </div>

            {/* Submit Button - ALWAYS PROMINENT AND VISIBLE */}
            <div className="form-action gsap-anim-item">
              <button
                type="submit"
                ref={submitBtnRef}
                className={`login-submit-btn ${isLoading ? 'btn-loading' : ''}`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="btn-content-loading">
                    <span className="btn-spinner" />
                    <span>Đang xác thực...</span>
                  </span>
                ) : (
                  <span className="btn-content">
                    <span>Đăng nhập vào hệ thống</span>
                    <ArrowRightIcon size={18} className="btn-arrow" />
                  </span>
                )}
              </button>
            </div>
          </form>

          {/* Quick Demo Credentials Section */}
          <div className="demo-accounts-section gsap-anim-item">
            <div className="demo-divider">
              <span className="demo-divider-line" />
              <span className="demo-divider-text">
                <BoltIcon size={15} className="demo-icon" /> Tài khoản dùng thử nhanh
              </span>
              <span className="demo-divider-line" />
            </div>

            <div className="demo-grid">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.username}
                  type="button"
                  className={`demo-badge-btn ${acc.primary ? 'demo-badge-primary' : ''}`}
                  onClick={(e) => handleQuickFill(acc, e)}
                  title={`Dùng thử: ${acc.username} (${acc.balance})`}
                >
                  <div className="demo-badge-header">
                    <span className="demo-user-name">{acc.label}</span>
                    <span className={`demo-tag ${acc.primary ? 'tag-primary' : ''}`}>{acc.badge}</span>
                  </div>
                  <span className="demo-balance-text">{acc.balance}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="login-footer-note gsap-anim-item">
          <p>© 2026 iBanking TDTU — Kiến trúc Microservices SOA</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
