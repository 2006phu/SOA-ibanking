import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';
import { useAuth } from '../../contexts/AuthContext';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import './TuitionPayment.css';

const TuitionPayment = () => {
  const { user } = useAuth();
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
  
  // Result state
  const [result, setResult] = useState(null); // { success: boolean, data: any, message: string }

  // Timer effect for OTP
  useEffect(() => {
    let interval;
    if (step === 3 && timer > 0) {
      interval = setInterval(() => {
        setTimer((prevTimer) => prevTimer - 1);
      }, 1000);
    } else if (timer === 0 && step === 3) {
      setOtpError('Mã OTP đã hết hạn. Vui lòng thử lại.');
    }
    return () => clearInterval(interval);
  }, [step, timer]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!mssv) return;
    
    setIsSearching(true);
    setSearchError('');
    setStudentInfo(null);
    
    try {
      const response = await axiosClient.get(`/tuition/${mssv}`);
      if (response) {
        setStudentInfo({
          mssv: response.mssv,
          full_name: response.student_name,
          program: response.program,
          unpaid_fees: (response.tuition_fees || []).filter(f => f.status === 'UNPAID')
        });
      } else {
        setSearchError('Không tìm thấy thông tin sinh viên.');
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setSearchError('Không tìm thấy sinh viên với MSSV này.');
      } else {
        setSearchError(error.response?.data?.detail || 'Có lỗi xảy ra khi tra cứu học phí.');
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectFee = (fee) => {
    setSelectedFee(fee);
    setStep(2);
  };

  const handleInitiatePayment = async () => {
    if (!isAgreed || user.balance < selectedFee.amount) return;
    
    setIsInitiating(true);
    setConfirmError('');
    
    try {
      // 1. Khởi tạo giao dịch
      const response = await axiosClient.post('/payments/initiate', {
        mssv: studentInfo.mssv,
        tuition_fee_id: selectedFee.id
      });
      
      const txnId = response.transaction_id;
      setTransactionId(txnId);
      
      // 2. Gọi confirm để sinh mã OTP và đẩy qua RabbitMQ
      const confirmRes = await axiosClient.post(`/payments/${txnId}/confirm`);
      if (confirmRes && confirmRes.otp_code) {
        setDemoOtp(confirmRes.otp_code);
      }
      
      // 3. Chuyển sang bước nhập OTP
      setStep(3);
      setTimer(300); // Reset timer to 5 minutes
      setOtp(['', '', '', '', '', '']);
    } catch (error) {
      setConfirmError(error.response?.data?.detail || error.response?.data?.message || 'Không thể khởi tạo giao dịch.');
    } finally {
      setIsInitiating(false);
    }
  };

  const handleOtpChange = (element, index) => {
    if (isNaN(element.value)) return false;

    setOtp([...otp.map((d, idx) => (idx === index ? element.value : d))]);

    // Focus next input
    if (element.nextSibling && element.value) {
      element.nextSibling.focus();
    }
  };

  const handleVerifyOtp = async () => {
    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      setOtpError('Vui lòng nhập đủ 6 số OTP.');
      return;
    }
    
    setIsVerifying(true);
    setOtpError('');
    
    try {
      // In a real flow, you might call /verify-otp then /confirm, or /confirm directly with OTP
      // Following requirements: POST /api/payments/{transaction_id}/verify-otp {otp_code}
      const response = await axiosClient.post(`/payments/${transactionId}/verify-otp`, {
        otp_code: otpCode
      });
      
      setResult({
        success: true,
        data: response,
        message: 'Thanh toán thành công!'
      });
      setStep(4);
    } catch (error) {
      // If OTP fails but can retry
      setOtpError(error.response?.data?.message || 'Mã OTP không hợp lệ.');
      
      // If payment failed completely
      if (error.response?.data?.status === 'FAILED') {
        setResult({
          success: false,
          data: null,
          message: error.response?.data?.message || 'Giao dịch thất bại.'
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
  };

  return (
    <div className="payment-container">
      <div className="payment-header">
        <h1>Thanh toán học phí</h1>
        <div className="step-indicator">
          <div className={`step ${step >= 1 ? 'active' : ''}`}>1. Tra cứu</div>
          <div className={`step-line ${step >= 2 ? 'active' : ''}`}></div>
          <div className={`step ${step >= 2 ? 'active' : ''}`}>2. Xác nhận</div>
          <div className={`step-line ${step >= 3 ? 'active' : ''}`}></div>
          <div className={`step ${step >= 3 ? 'active' : ''}`}>3. Xác thực</div>
          <div className={`step-line ${step >= 4 ? 'active' : ''}`}></div>
          <div className={`step ${step >= 4 ? 'active' : ''}`}>4. Kết quả</div>
        </div>
      </div>

      {step === 1 && (
        <div className="card step-card">
          <h2>Tra cứu học phí sinh viên</h2>
          <form onSubmit={handleSearch} className="search-form">
            <div className="search-group">
              <input
                type="text"
                className="form-control"
                placeholder="Nhập mã số sinh viên (MSSV)"
                value={mssv}
                onChange={(e) => setMssv(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-primary" disabled={isSearching || !mssv}>
                {isSearching ? 'Đang tra cứu...' : 'Tra cứu'}
              </button>
            </div>
            {searchError && <div className="error-message">{searchError}</div>}
          </form>

          {studentInfo && (
            <div className="student-info-section">
              <div className="student-details">
                <p><strong>Họ và tên:</strong> {studentInfo.full_name}</p>
                <p><strong>MSSV:</strong> {studentInfo.mssv}</p>
                <p><strong>Chương trình:</strong> {studentInfo.program || 'Chính quy'}</p>
              </div>

              <h3>Danh sách học phí chưa thanh toán</h3>
              {studentInfo.unpaid_fees && studentInfo.unpaid_fees.length > 0 ? (
                <div className="fee-list">
                  {studentInfo.unpaid_fees.map((fee) => (
                    <div key={fee.id} className="fee-item">
                      <div className="fee-info">
                        <h4>{fee.semester || 'Học kỳ không xác định'}</h4>
                        <p className="fee-amount">{formatCurrency(fee.amount)}</p>
                      </div>
                      <button 
                        className="btn btn-primary"
                        onClick={() => handleSelectFee(fee)}
                      >
                        Thanh toán
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-fees-message">
                  Không có khoản học phí nào cần thanh toán.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {step === 2 && selectedFee && (
        <div className="card step-card confirm-step">
          <h2>Xác nhận giao dịch</h2>
          
          <div className="confirm-details">
            <div className="detail-section">
              <h3>Thông tin người nộp tiền</h3>
              <div className="detail-row">
                <span className="label">Họ và tên:</span>
                <span className="value">{user.full_name}</span>
              </div>
              <div className="detail-row">
                <span className="label">Số điện thoại:</span>
                <span className="value">{user.phone}</span>
              </div>
              <div className="detail-row">
                <span className="label">Địa chỉ email:</span>
                <span className="value">{user.email}</span>
              </div>
            </div>

            <div className="detail-section">
              <h3>Thông tin học phí</h3>
              <div className="detail-row">
                <span className="label">MSSV:</span>
                <span className="value">{studentInfo.mssv}</span>
              </div>
              <div className="detail-row">
                <span className="label">Họ và tên sinh viên:</span>
                <span className="value">{studentInfo.full_name}</span>
              </div>
              <div className="detail-row">
                <span className="label">Học kỳ:</span>
                <span className="value">{selectedFee.semester}</span>
              </div>
              <div className="detail-row highlight">
                <span className="label">Số tiền cần thanh toán:</span>
                <span className="value amount">{formatCurrency(selectedFee.amount)}</span>
              </div>
            </div>

            <div className="detail-section payment-info">
              <h3>Thông tin thanh toán</h3>
              <div className="detail-row">
                <span className="label">Số dư hiện tại:</span>
                <span className="value">{formatCurrency(user.balance)}</span>
              </div>
              
              {user.balance < selectedFee.amount && (
                <div className="balance-warning">
                  Số dư tài khoản không đủ để thực hiện giao dịch này.
                </div>
              )}

              <div className="agreement-checkbox">
                <input
                  type="checkbox"
                  id="agreement"
                  checked={isAgreed}
                  onChange={(e) => setIsAgreed(e.target.checked)}
                  disabled={user.balance < selectedFee.amount}
                />
                <label htmlFor="agreement">
                  Tôi đồng ý với các thỏa thuận và điều khoản thanh toán
                </label>
              </div>
            </div>
          </div>

          {confirmError && <div className="error-message">{confirmError}</div>}

          <div className="step-actions">
            <button className="btn btn-secondary" onClick={() => setStep(1)} disabled={isInitiating}>
              Quay lại
            </button>
            <button
              className="btn btn-primary"
              onClick={handleInitiatePayment}
              disabled={!isAgreed || user.balance < selectedFee.amount || isInitiating}
            >
              {isInitiating ? 'Đang xử lý...' : 'Xác nhận giao dịch'}
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card step-card otp-step">
          <h2>Xác thực OTP</h2>
          <p className="otp-message">
            Mã OTP đã được gửi đến email <strong>{user.email}</strong> của bạn
          </p>
          
          <div className="otp-container">
            {otp.map((data, index) => (
              <input
                className="otp-input"
                type="text"
                name="otp"
                maxLength="1"
                key={index}
                value={data}
                onChange={e => handleOtpChange(e.target, index)}
                onFocus={e => e.target.select()}
                disabled={timer === 0 || isVerifying}
              />
            ))}
          </div>
          
          <div className="timer">
            Thời gian còn lại: {Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, '0')}
          </div>
          
          {otpError && <div className="error-message">{otpError}</div>}
          
          <div className="step-actions">
            <button 
              className="btn btn-primary" 
              onClick={handleVerifyOtp}
              disabled={otp.join('').length !== 6 || timer === 0 || isVerifying}
            >
              {isVerifying ? 'Đang xác thực...' : 'Xác nhận'}
            </button>
          </div>
        </div>
      )}

      {step === 4 && result && (
        <div className="card step-card result-step">
          <div className={`result-icon ${result.success ? 'success' : 'error'}`}>
            {result.success ? '✓' : '✕'}
          </div>
          <h2>{result.message}</h2>
          
          {result.success && result.data && (
            <div className="result-details">
              <div className="detail-row">
                <span className="label">Mã giao dịch:</span>
                <span className="value">{result.data.transaction_id || transactionId}</span>
              </div>
              <div className="detail-row">
                <span className="label">Số tiền:</span>
                <span className="value">{formatCurrency(selectedFee.amount)}</span>
              </div>
              <div className="detail-row">
                <span className="label">Số dư còn lại:</span>
                <span className="value">{formatCurrency(user.balance - selectedFee.amount)}</span>
              </div>
              <div className="detail-row">
                <span className="label">Thời gian:</span>
                <span className="value">{formatDateTime(new Date().toISOString())}</span>
              </div>
            </div>
          )}

          <div className="step-actions">
            <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
              Về trang chủ
            </button>
            {result.success ? (
              <button className="btn btn-primary" onClick={resetFlow}>
                Thanh toán tiếp
              </button>
            ) : (
              <button className="btn btn-primary" onClick={() => setStep(2)}>
                Thử lại
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TuitionPayment;
