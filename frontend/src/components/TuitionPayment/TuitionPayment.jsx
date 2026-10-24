import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../common/Toast';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import './TuitionPayment.css';

const TuitionPayment = () => {
  const { user, refreshUser } = useAuth();
  const { success, error: toastError, info } = useToast();
  const navigate = useNavigate();

  // Step state: 1 (Search), 2 (Confirm), 3 (OTP), 4 (Result)
  const [step, setStep] = useState(1);

  // Search state
  const [mssv, setMssv] = useState('');
  const [studentInfo, setStudentInfo] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState('');

  // Selected fee state
  const [selectedFee, setSelectedFee] = useState(null);

  // Confirm state
  const [isAgreed, setIsAgreed] = useState(false);
  const [transactionId, setTransactionId] = useState(null);
  const [isInitiating, setIsInitiating] = useState(false);
  const [confirmError, setConfirmError] = useState('');
  const [demoOtp, setDemoOtp] = useState('');

  // OTP state
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [timer, setTimer] = useState(300); // 5 minutes
  const [isVerifying, setIsVerifying] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);

  // Result state
  const [result, setResult] = useState(null);

  const otpInputRefs = useRef([]);

  // Timer effect for OTP
  useEffect(() => {
    let interval;
    if (step === 3 && timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    } else if (timer === 0 && step === 3) {
      setOtpError('Mã OTP đã hết hiệu lực (quá 5 phút). Vui lòng nhấn "Gửi lại mã OTP".');
    }
    return () => clearInterval(interval);
  }, [step, timer]);

  // Resend cooldown timer
  useEffect(() => {
    let interval;
    if (resendCooldown > 0) {
      interval = setInterval(() => {
        setResendCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [resendCooldown]);

  const handleSearch = async (e, customMssv = null) => {
    if (e) e.preventDefault();
    const queryMssv = (customMssv || mssv).trim();
    if (!queryMssv) return;

    setMssv(queryMssv);
    setIsSearching(true);
    setSearchError('');
    setStudentInfo(null);

    try {
      const response = await axiosClient.get(`/tuition/${queryMssv}`);
      if (response) {
        const unpaid = (response.tuition_fees || []).filter((f) => f.status === 'UNPAID');
        setStudentInfo({
          mssv: response.mssv,
          full_name: response.student_name,
          program: response.program,
          unpaid_fees: unpaid,
        });
        if (unpaid.length === 0) {
          info('Sinh viên này hiện đã hoàn thành toàn bộ học phí!');
        }
      } else {
        setSearchError('Không tìm thấy thông tin sinh viên.');
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setSearchError(`Không tìm thấy sinh viên với MSSV "${queryMssv}".`);
      } else {
        setSearchError(err.response?.data?.detail || 'Có lỗi xảy ra khi tra cứu học phí.');
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectFee = (fee) => {
    setSelectedFee(fee);
    setStep(2);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleInitiatePayment = async () => {
    if (!isAgreed || user.balance < selectedFee.amount) return;

    setIsInitiating(true);
    setConfirmError('');

    try {
      // 1. Khởi tạo giao dịch
      const response = await axiosClient.post('/payments/initiate', {
        mssv: studentInfo.mssv,
        tuition_fee_id: selectedFee.id,
      });

      const txnId = response.transaction_id;
      setTransactionId(txnId);

      // 2. Gọi confirm để sinh mã OTP và phát tin nhắn qua RabbitMQ
      const confirmRes = await axiosClient.post(`/payments/${txnId}/confirm`);
      if (confirmRes && confirmRes.otp_code) {
        setDemoOtp(confirmRes.otp_code);
      }

      setStep(3);
      setTimer(300);
      setResendCooldown(60);
      setOtp(['', '', '', '', '', '']);
      info(`Mã OTP đã được gửi về email ${user.email}!`);
      setTimeout(() => otpInputRefs.current[0]?.focus(), 150);
    } catch (err) {
      setConfirmError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Không thể khởi tạo giao dịch thanh toán.'
      );
    } finally {
      setIsInitiating(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendCooldown > 0 || !transactionId) return;
    try {
      const confirmRes = await axiosClient.post(`/payments/${transactionId}/confirm`);
      if (confirmRes && confirmRes.otp_code) {
        setDemoOtp(confirmRes.otp_code);
      }
      setTimer(300);
      setResendCooldown(60);
      setOtp(['', '', '', '', '', '']);
      setOtpError('');
      success(`Đã gửi lại mã OTP mới đến email ${user.email}!`);
      otpInputRefs.current[0]?.focus();
    } catch (err) {
      toastError('Không thể gửi lại mã OTP. Vui lòng thử lại.');
    }
  };

  const handleOtpChange = (val, index) => {
    if (!/^\d*$/.test(val)) return;

    const newOtp = [...otp];
    newOtp[index] = val.slice(-1);
    setOtp(newOtp);

    // Auto focus next
    if (val && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (e, index) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').trim();
    if (/^\d{6}$/.test(pasted)) {
      const digits = pasted.split('');
      setOtp(digits);
      otpInputRefs.current[5]?.focus();
    }
  };

  const handleFillDemoOtp = () => {
    if (demoOtp && demoOtp.length === 6) {
      setOtp(demoOtp.split(''));
      success('Đã tự động điền mã OTP thử nghiệm!');
    }
  };

  const handleVerifyOtp = async () => {
    const code = otp.join('');
    if (code.length !== 6) {
      setOtpError('Vui lòng nhập đầy đủ 6 chữ số OTP.');
      return;
    }

    setIsVerifying(true);
    setOtpError('');

    try {
      const response = await axiosClient.post(`/payments/${transactionId}/verify-otp`, {
        otp_code: code,
      });

      if (refreshUser) {
        await refreshUser();
      }

      setResult({
        success: true,
        data: response,
        message: 'Giao dịch thanh toán học phí thành công!',
      });
      setStep(4);
      success('Thanh toán thành công! Biên lai điện tử đã được ghi nhận.');
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data?.message || 'Xác thực OTP thất bại.';
      setOtpError(detail);

      if (err.response?.status === 409 || err.response?.data?.status === 'FAILED' || err.response?.data?.status === 'REFUNDED') {
        setResult({
          success: false,
          data: null,
          message: detail,
        });
        setStep(4);
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const resetFlow = () => {
    setStep(1);
    setMssv('');
    setStudentInfo(null);
    setSelectedFee(null);
    setIsAgreed(false);
    setDemoOtp('');
    setResult(null);
    setOtpError('');
    setConfirmError('');
  };

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercentage = ((step - 1) / 3) * 100;

  return (
    <div className="payment-container">
      {/* Header */}
      <div className="payment-header">
        <h1>Nộp học phí sinh viên</h1>
        <p>Thanh toán toàn bộ công nợ học phí nhanh chóng và bảo mật qua mã xác thực OTP</p>

        {/* Stepper Bar */}
        <div className="stepper-bar">
          <div className="stepper-connector">
            <div
              className="stepper-connector-fill"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>

          <div className={`step-node ${step === 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <div className="step-circle">{step > 1 ? '✓' : '1'}</div>
            <span className="step-label">Tra cứu</span>
          </div>

          <div className={`step-node ${step === 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            <div className="step-circle">{step > 2 ? '✓' : '2'}</div>
            <span className="step-label">Xác nhận</span>
          </div>

          <div className={`step-node ${step === 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}>
            <div className="step-circle">{step > 3 ? '✓' : '3'}</div>
            <span className="step-label">Xác thực OTP</span>
          </div>

          <div className={`step-node ${step === 4 ? 'active' : ''}`}>
            <div className="step-circle">4</div>
            <span className="step-label">Hoàn tất</span>
          </div>
        </div>
      </div>

      {/* STEP 1: Search Student & Display Unpaid Fees */}
      {step === 1 && (
        <div className="card">
          <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Tra cứu học phí theo MSSV</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            Nhập Mã số sinh viên (MSSV) để hệ thống tra cứu công nợ các học kỳ chưa đóng
          </p>

          <form onSubmit={(e) => handleSearch(e)}>
            <div className="form-group">
              <label htmlFor="mssv-input" className="form-label">Mã số sinh viên (MSSV)</label>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <input
                  id="mssv-input"
                  type="text"
                  className="form-control text-mono"
                  placeholder="Ví dụ: 52100888, 52100999..."
                  value={mssv}
                  onChange={(e) => setMssv(e.target.value)}
                  autoFocus
                />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSearching || !mssv.trim()}
                  style={{ minWidth: '130px' }}
                >
                  {isSearching ? 'Đang tìm...' : '🔍 Tra cứu'}
                </button>
              </div>

              {/* Quick suggestions */}
              <div className="quick-mssv-container">
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Gợi ý nhanh:</span>
                <button
                  type="button"
                  className="quick-mssv-chip"
                  onClick={(e) => handleSearch(e, '52100888')}
                >
                  52100888 (Nguyễn Văn An)
                </button>
                <button
                  type="button"
                  className="quick-mssv-chip"
                  onClick={(e) => handleSearch(e, '52100999')}
                >
                  52100999 (Trần Thị Bích)
                </button>
                <button
                  type="button"
                  className="quick-mssv-chip"
                  onClick={(e) => handleSearch(e, '52100777')}
                >
                  52100777 (Lê Hoàng Nam)
                </button>
              </div>
            </div>
          </form>

          {searchError && (
            <div className="login-error" style={{ marginTop: '1rem' }}>
              <span>⚠️</span>
              <div>{searchError}</div>
            </div>
          )}

          {studentInfo && (
            <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h4 style={{ fontSize: '1.1rem', color: 'var(--text-main)' }}>{studentInfo.full_name}</h4>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    MSSV: <strong>{studentInfo.mssv}</strong> • Ngành: {studentInfo.program || 'Công nghệ Thông tin'}
                  </span>
                </div>
                <span className="badge badge-info">
                  <span className="badge-dot"></span> {studentInfo.unpaid_fees.length} khoản nợ
                </span>
              </div>

              {studentInfo.unpaid_fees.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', background: '#f8fafc', borderRadius: '12px' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🎉</div>
                  <h4 style={{ color: '#059669', marginBottom: '0.25rem' }}>Không có khoản nợ nào!</h4>
                  <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
                    Sinh viên {studentInfo.full_name} ({studentInfo.mssv}) đã hoàn thành toàn bộ học phí.
                  </p>
                </div>
              ) : (
                <div className="fee-cards-list">
                  {studentInfo.unpaid_fees.map((fee) => (
                    <div key={fee.id} className="fee-card-item">
                      <div className="fee-info-col">
                        <h4>{fee.semester}</h4>
                        <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                          Hình thức: Đóng toàn bộ một lần
                        </div>
                        <div className="fee-amount-display" style={{ marginTop: '0.4rem' }}>
                          {formatCurrency(fee.amount)}
                        </div>
                      </div>
                      <div>
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => handleSelectFee(fee)}
                        >
                          Chọn thanh toán →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* STEP 2: Confirmation & Breakdown */}
      {step === 2 && selectedFee && studentInfo && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem' }}>Xác nhận thông tin giao dịch</h3>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setStep(1)}
            >
              ← Thay đổi khoản nộp
            </button>
          </div>

          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Vui lòng kiểm tra kỹ chi tiết khoản học phí và số dư tài khoản của bạn trước khi nhận mã OTP.
          </p>

          <div className="bill-breakdown-card">
            <div className="bill-row">
              <span style={{ color: 'var(--text-secondary)' }}>Sinh viên thụ hưởng</span>
              <span style={{ fontWeight: 600 }}>{studentInfo.full_name} ({studentInfo.mssv})</span>
            </div>
            <div className="bill-row">
              <span style={{ color: 'var(--text-secondary)' }}>Học kỳ thanh toán</span>
              <span style={{ fontWeight: 600 }}>{selectedFee.semester}</span>
            </div>
            <div className="bill-row">
              <span style={{ color: 'var(--text-secondary)' }}>Số dư tài khoản hiện tại</span>
              <span className="text-mono" style={{ fontWeight: 600 }}>{formatCurrency(user.balance)}</span>
            </div>
            <div className="bill-row total-row">
              <span style={{ fontSize: '1.05rem', fontWeight: 700 }}>Tổng tiền thanh toán</span>
              <span className="fee-amount-display" style={{ fontSize: '1.4rem' }}>
                {formatCurrency(selectedFee.amount)}
              </span>
            </div>
          </div>

          {/* Balance check alert */}
          {user.balance >= selectedFee.amount ? (
            <div className="balance-check-alert balance-ok">
              <span>✅</span>
              <div>
                Số dư tài khoản đủ để thực hiện thanh toán. Sau khi thanh toán, số dư ước tính còn:{' '}
                <strong>{formatCurrency(user.balance - selectedFee.amount)}</strong>.
              </div>
            </div>
          ) : (
            <div className="balance-check-alert balance-insufficient">
              <span>⚠️</span>
              <div>
                <strong>Số dư không đủ:</strong> Cần thêm{' '}
                <strong>{formatCurrency(selectedFee.amount - user.balance)}</strong> để thanh toán. Vui lòng nạp thêm tiền hoặc dùng tài khoản khác.
              </div>
            </div>
          )}

          {confirmError && (
            <div className="login-error" style={{ margin: '1rem 0' }}>
              <span>⚠️</span>
              <div>{confirmError}</div>
            </div>
          )}

          {/* Terms Agreement */}
          <div style={{ margin: '1.5rem 0', display: 'flex', alignItems: 'flex-start', gap: '0.65rem' }}>
            <input
              type="checkbox"
              id="agree-checkbox"
              checked={isAgreed}
              onChange={(e) => setIsAgreed(e.target.checked)}
              style={{ width: '18px', height: '18px', marginTop: '2px', cursor: 'pointer' }}
            />
            <label htmlFor="agree-checkbox" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              Tôi xác nhận thông tin thanh toán là chính xác và đồng ý trích nợ tài khoản để thanh toán khoản học phí này.
            </label>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setStep(1)}
              disabled={isInitiating}
            >
              Hủy bỏ
            </button>
            <button
              type="button"
              className="btn btn-primary"
              disabled={isInitiating || !isAgreed || user.balance < selectedFee.amount}
              onClick={handleInitiatePayment}
            >
              {isInitiating ? 'Đang gửi mã OTP...' : 'Nhận mã OTP qua Email →'}
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: 2FA Email OTP Verification */}
      {step === 3 && (
        <div className="card" style={{ maxWidth: '580px', margin: '0 auto', width: '100%' }}>
          <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🔐</div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: '0.35rem' }}>Xác thực mã OTP</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Mã bảo mật 6 số đã được gửi tới hòm thư:{' '}
              <strong style={{ color: 'var(--primary-700)' }}>{user.email}</strong>
            </p>
          </div>

          {/* Quick Demo OTP Chip */}
          {demoOtp && (
            <div className="demo-otp-badge">
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1e40af', textTransform: 'uppercase' }}>
                  ⚡ Mã OTP thực nghiệm (Demo):
                </span>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 800, color: '#1e3a8a', letterSpacing: '2px' }}>
                  {demoOtp}
                </div>
              </div>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={handleFillDemoOtp}
              >
                Tự động điền 📋
              </button>
            </div>
          )}

          {/* 6-box OTP Input */}
          <div className="otp-boxes-wrapper" onPaste={handleOtpPaste}>
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (otpInputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                className="otp-digit-input"
                value={digit}
                onChange={(e) => handleOtpChange(e.target.value, index)}
                onKeyDown={(e) => handleOtpKeyDown(e, index)}
              />
            ))}
          </div>

          {/* Timer Display */}
          <div className="otp-timer-container">
            <span>Hiệu lực còn: </span>
            <span
              className="otp-timer-val"
              style={{
                color: timer > 120 ? '#059669' : timer > 60 ? '#d97706' : '#dc2626',
              }}
            >
              {formatTimer(timer)}
            </span>
          </div>

          {otpError && (
            <div className="login-error" style={{ marginBottom: '1.25rem' }}>
              <span>⚠️</span>
              <div>{otpError}</div>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.85rem' }}
              disabled={isVerifying || otp.join('').length !== 6 || timer === 0}
              onClick={handleVerifyOtp}
            >
              {isVerifying ? 'Đang xử lý giao dịch Saga...' : 'Xác nhận thanh toán'}
            </button>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setStep(2)}
                disabled={isVerifying}
              >
                ← Quay lại
              </button>

              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleResendOtp}
                disabled={resendCooldown > 0 || isVerifying}
              >
                {resendCooldown > 0 ? `Gửi lại mã (${resendCooldown}s)` : 'Gửi lại mã OTP 🔄'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: Result & Electronic Receipt */}
      {step === 4 && result && (
        <div className="receipt-card" style={{ maxWidth: '600px', margin: '0 auto', width: '100%' }}>
          {result.success ? (
            <div>
              <div className="receipt-success-badge">✓</div>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <span className="badge badge-success" style={{ marginBottom: '0.5rem' }}>
                  Giao dịch thành công
                </span>
                <h2 style={{ fontSize: '1.5rem', color: '#0f172a' }}>Biên lai nộp học phí điện tử</h2>
                <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
                  Khoản tiền đã được ghi nhận vào hệ thống học vụ TDTU
                </p>
              </div>

              <div className="bill-breakdown-card" style={{ background: '#f8fafc' }}>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Mã giao dịch (TxID)</span>
                  <span className="text-mono" style={{ fontWeight: 600, fontSize: '0.8rem' }}>
                    {result.data?.transaction_id || transactionId}
                  </span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Sinh viên</span>
                  <span style={{ fontWeight: 600 }}>{studentInfo?.full_name} ({studentInfo?.mssv})</span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Học kỳ</span>
                  <span style={{ fontWeight: 600 }}>{selectedFee?.semester}</span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Số tiền đã nộp</span>
                  <span className="fee-amount-display" style={{ fontSize: '1.25rem', color: '#059669' }}>
                    {formatCurrency(result.data?.amount || selectedFee?.amount)}
                  </span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Số dư sau thanh toán</span>
                  <span className="text-mono" style={{ fontWeight: 600 }}>
                    {formatCurrency(result.data?.balance_after ?? user.balance)}
                  </span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Thời gian thực hiện</span>
                  <span style={{ fontSize: '0.85rem' }}>
                    {formatDateTime(result.data?.completed_at || new Date().toISOString())}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => window.print()}
                >
                  🖨️ In biên lai
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  onClick={() => navigate('/dashboard')}
                >
                  Về trang chủ
                </button>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '3.5rem', marginBottom: '0.5rem' }}>❌</div>
              <h2 style={{ color: '#e11d48', marginBottom: '0.5rem' }}>Giao dịch thất bại</h2>
              <p style={{ color: '#64748b', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
                {result.message}
              </p>

              <div style={{ background: '#fef2f2', border: '1px solid #fecdd3', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.85rem', color: '#9f1239' }}>
                💡 Hệ thống đã tự động thực hiện cơ chế bù trừ (Saga Rollback) để bảo vệ số dư tài khoản của bạn.
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={resetFlow}
                >
                  Thử lại
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  onClick={() => navigate('/dashboard')}
                >
                  Về trang chủ
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TuitionPayment;
