export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null) return '0 VND';
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND'
  }).format(amount);
};

export const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return new Intl.DateTimeFormat('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date);
};

export const formatTransactionStatus = (status) => {
  switch (status) {
    case 'SUCCESS':
      return { label: 'Thành công', color: 'green', className: 'status-success' };
    case 'FAILED':
      return { label: 'Thất bại', color: 'red', className: 'status-failed' };
    case 'PENDING':
      return { label: 'Đang xử lý', color: 'orange', className: 'status-pending' };
    default:
      return { label: status, color: 'gray', className: 'status-default' };
  }
};
