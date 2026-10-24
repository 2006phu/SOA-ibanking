export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null) return '0 ₫';
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND'
  }).format(amount);
};

export const formatDateTime = (isoString) => {
  if (!isoString) return '---';
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;
    return new Intl.DateTimeFormat('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  } catch (e) {
    return isoString;
  }
};

export const formatTransactionStatus = (status) => {
  switch (status?.toUpperCase()) {
    case 'SUCCESS':
      return { label: 'Thành công', color: 'emerald', className: 'status-success', badgeBg: '#dcfce7', badgeText: '#15803d' };
    case 'REFUNDED':
      return { label: 'Đã hoàn tiền', color: 'amber', className: 'status-refunded', badgeBg: '#fef3c7', badgeText: '#b45309' };
    case 'FAILED':
      return { label: 'Thất bại', color: 'rose', className: 'status-failed', badgeBg: '#ffe4e6', badgeText: '#be123c' };
    case 'OTP_SENT':
      return { label: 'Chờ xác thực OTP', color: 'blue', className: 'status-otp', badgeBg: '#dbeafe', badgeText: '#1d4ed8' };
    case 'PENDING':
      return { label: 'Đang xử lý', color: 'indigo', className: 'status-pending', badgeBg: '#e0e7ff', badgeText: '#4338ca' };
    default:
      return { label: status || 'Không rõ', color: 'slate', className: 'status-default', badgeBg: '#f1f5f9', badgeText: '#475569' };
  }
};
