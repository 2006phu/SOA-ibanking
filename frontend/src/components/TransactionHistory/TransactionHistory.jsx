import React, { useState, useEffect } from 'react';
import axiosClient from '../../api/axiosClient';
import { formatCurrency, formatDateTime, formatTransactionStatus } from '../../utils/formatters';
import './TransactionHistory.css';
import Loading from '../common/Loading';

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const size = 10;

  useEffect(() => {
    const fetchTransactions = async () => {
      setLoading(true);
      try {
        const response = await axiosClient.get(`/users/me/transactions?page=${page}&size=${size}`);
        setTransactions(response.items || []);
        setTotalPages(response.total_pages || 1);
      } catch (err) {
        setError('Không thể tải lịch sử giao dịch. Vui lòng thử lại sau.');
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [page]);

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage(page + 1);
  };

  if (loading && transactions.length === 0) return <Loading />;

  return (
    <div className="history-container">
      <div className="history-header">
        <h1>Lịch sử giao dịch</h1>
      </div>

      <div className="card history-card">
        {error && <div className="error-message mb-3">{error}</div>}

        {transactions.length === 0 && !loading && !error ? (
          <div className="no-data">Bạn chưa có giao dịch nào.</div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>STT</th>
                    <th>Mã GD</th>
                    <th>MSSV</th>
                    <th>Tên SV</th>
                    <th>Số tiền</th>
                    <th>Thời gian</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx, index) => {
                    const statusInfo = formatTransactionStatus(tx.status || 'SUCCESS');
                    return (
                      <tr key={tx.id || tx.transaction_id || index}>
                        <td>{(page - 1) * size + index + 1}</td>
                        <td className="tx-id">{tx.id || tx.transaction_id}</td>
                        <td>{tx.mssv || '---'}</td>
                        <td>{tx.student_name || '---'}</td>
                        <td className="amount">{formatCurrency(tx.amount)}</td>
                        <td>{formatDateTime(tx.created_at || tx.completed_at)}</td>
                        <td>
                          <span className={`status-badge ${statusInfo.className}`}>
                            {statusInfo.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button 
                  className="btn btn-secondary btn-sm" 
                  onClick={handlePrevPage} 
                  disabled={page === 1}
                >
                  Trang trước
                </button>
                <span className="page-info">
                  Trang {page} / {totalPages}
                </span>
                <button 
                  className="btn btn-secondary btn-sm" 
                  onClick={handleNextPage} 
                  disabled={page === totalPages}
                >
                  Trang sau
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TransactionHistory;
