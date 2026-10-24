import React, { useState, useEffect } from 'react';
import axiosClient from '../../api/axiosClient';
import { formatCurrency, formatDateTime, formatTransactionStatus } from '../../utils/formatters';
import Loading from '../common/Loading';
import './TransactionHistory.css';

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Filter & Search
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Transaction for Modal Receipt View
  const [selectedTx, setSelectedTx] = useState(null);

  const size = 10;

  useEffect(() => {
    const fetchTransactions = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await axiosClient.get(`/users/me/transactions?page=${page}&size=${size}`);
        setTransactions(response.items || []);
        setTotalPages(response.total_pages || 1);
        setTotalCount(response.total || (response.items || []).length);
      } catch (err) {
        setError('Không thể tải lịch sử giao dịch. Vui lòng thử lại sau.');
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [page]);

  const filteredTransactions = transactions.filter((tx) => {
    const matchesStatus =
      statusFilter === 'ALL' || (tx.status || 'SUCCESS').toUpperCase() === statusFilter;
    const query = searchQuery.trim().toLowerCase();
    const matchesSearch =
      !query ||
      (tx.mssv && tx.mssv.toLowerCase().includes(query)) ||
      (tx.student_name && tx.student_name.toLowerCase().includes(query)) ||
      (tx.id && tx.id.toLowerCase().includes(query)) ||
      (tx.transaction_id && tx.transaction_id.toLowerCase().includes(query));

    return matchesStatus && matchesSearch;
  });

  return (
    <div className="history-container">
      {/* Header */}
      <div className="history-header">
        <div>
          <h1>Lịch sử giao dịch</h1>
          <p>Xem lại tất cả các giao dịch thanh toán học phí và đối soát biên lai điện tử</p>
        </div>
        <div>
          <span className="badge badge-info">
            <span className="badge-dot"></span> Tổng cộng: {totalCount} giao dịch
          </span>
        </div>
      </div>

      <div className="card">
        {/* Controls: Filter Chips & Search Bar */}
        <div className="history-controls">
          <div className="filter-chips">
            <button
              type="button"
              className={`filter-chip-btn ${statusFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setStatusFilter('ALL')}
            >
              Tất cả
            </button>
            <button
              type="button"
              className={`filter-chip-btn ${statusFilter === 'SUCCESS' ? 'active' : ''}`}
              onClick={() => setStatusFilter('SUCCESS')}
            >
              ✅ Thành công
            </button>
            <button
              type="button"
              className={`filter-chip-btn ${statusFilter === 'REFUNDED' ? 'active' : ''}`}
              onClick={() => setStatusFilter('REFUNDED')}
            >
              🔄 Đã hoàn tiền
            </button>
            <button
              type="button"
              className={`filter-chip-btn ${statusFilter === 'FAILED' ? 'active' : ''}`}
              onClick={() => setStatusFilter('FAILED')}
            >
              ❌ Thất bại
            </button>
          </div>

          <input
            type="text"
            className="history-search-input"
            placeholder="🔍 Tìm theo MSSV, tên SV, TxID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {error && (
          <div className="login-error" style={{ marginBottom: '1.25rem' }}>
            <span>⚠️</span>
            <div>{error}</div>
          </div>
        )}

        {loading ? (
          <div style={{ padding: '3rem 0', textAlign: 'center' }}>
            <Loading />
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>📭</div>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', marginBottom: '0.25rem' }}>
              Không tìm thấy giao dịch nào
            </h3>
            <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
              {searchQuery || statusFilter !== 'ALL'
                ? 'Hãy thử thay đổi bộ lọc hoặc từ khóa tìm kiếm.'
                : 'Bạn chưa thực hiện giao dịch thanh toán nào.'}
            </p>
          </div>
        ) : (
          <div className="history-table-wrapper">
            <table className="modern-table">
              <thead>
                <tr>
                  <th>STT</th>
                  <th>Mã giao dịch</th>
                  <th>MSSV</th>
                  <th>Tên sinh viên</th>
                  <th>Số tiền</th>
                  <th>Thời gian</th>
                  <th>Trạng thái</th>
                  <th style={{ textAlign: 'right' }}>Chi tiết</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((tx, index) => {
                  const statusInfo = formatTransactionStatus(tx.status || 'SUCCESS');
                  const txId = tx.id || tx.transaction_id || `tx-${index}`;

                  return (
                    <tr key={txId} onClick={() => setSelectedTx(tx)}>
                      <td>{(page - 1) * size + index + 1}</td>
                      <td className="tx-id-cell" title={txId}>
                        {txId.slice(0, 10)}...
                      </td>
                      <td style={{ fontWeight: 600 }}>{tx.mssv || '---'}</td>
                      <td>{tx.student_name || '---'}</td>
                      <td className="amount-cell">{formatCurrency(tx.amount)}</td>
                      <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        {formatDateTime(tx.created_at || tx.completed_at)}
                      </td>
                      <td>
                        <span
                          className={`badge ${statusInfo.className}`}
                          style={{
                            background: statusInfo.badgeBg,
                            color: statusInfo.badgeText,
                            border: 'none',
                          }}
                        >
                          <span className="badge-dot" style={{ background: statusInfo.badgeText }}></span>
                          {statusInfo.label}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span style={{ color: 'var(--primary-600)', fontWeight: 600, fontSize: '0.8rem' }}>
                          Xem biên lai →
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="pagination-bar">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              ← Trang trước
            </button>
            <span className="page-indicator">
              Trang <strong>{page}</strong> / {totalPages}
            </span>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Trang tiếp →
            </button>
          </div>
        )}
      </div>

      {/* Electronic Receipt Modal */}
      {selectedTx && (
        <div className="modal-overlay" onClick={() => setSelectedTx(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-receipt-header">
              <div>
                <h3 style={{ fontSize: '1.2rem', color: '#ffffff', marginBottom: '2px' }}>
                  Biên lai giao dịch điện tử
                </h3>
                <span style={{ fontSize: '0.75rem', color: '#bfdbfe' }}>iBanking TDTU e-Receipt</span>
              </div>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setSelectedTx(null)}
              >
                ✕
              </button>
            </div>

            <div className="modal-receipt-body">
              <div style={{ textAlign: 'center', margin: '0.5rem 0 1.5rem' }}>
                <span
                  className="badge"
                  style={{
                    background: formatTransactionStatus(selectedTx.status).badgeBg,
                    color: formatTransactionStatus(selectedTx.status).badgeText,
                    fontSize: '0.85rem',
                    padding: '0.35rem 0.85rem',
                  }}
                >
                  {formatTransactionStatus(selectedTx.status).label}
                </span>
                <div
                  className="fee-amount-display"
                  style={{ fontSize: '1.75rem', marginTop: '0.5rem', color: '#0f172a' }}
                >
                  {formatCurrency(selectedTx.amount)}
                </div>
              </div>

              <div className="bill-breakdown-card" style={{ margin: 0 }}>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Mã giao dịch</span>
                  <span className="text-mono" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                    {selectedTx.id || selectedTx.transaction_id}
                  </span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Sinh viên</span>
                  <span style={{ fontWeight: 600 }}>{selectedTx.student_name || '---'}</span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>MSSV</span>
                  <span style={{ fontWeight: 600 }}>{selectedTx.mssv || '---'}</span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Nội dung</span>
                  <span style={{ fontWeight: 500 }}>
                    {selectedTx.description || `Thanh toán học phí MSSV ${selectedTx.mssv}`}
                  </span>
                </div>
                <div className="bill-row">
                  <span style={{ color: '#64748b' }}>Thời gian</span>
                  <span style={{ fontSize: '0.85rem' }}>
                    {formatDateTime(selectedTx.created_at || selectedTx.completed_at)}
                  </span>
                </div>
              </div>
            </div>

            <div className="modal-receipt-footer">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => window.print()}
              >
                🖨️ In biên lai
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => setSelectedTx(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionHistory;
