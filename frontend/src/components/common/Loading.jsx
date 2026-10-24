import React from 'react';

const Loading = ({ fullScreen = false, message = 'Đang tải dữ liệu...' }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '0.85rem',
        minHeight: fullScreen ? '100vh' : '220px',
        padding: '2rem',
      }}
    >
      <div
        className="spinner"
        style={{
          border: '3px solid #e2e8f0',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          borderLeftColor: '#2563eb',
          animation: 'spin 0.8s linear infinite',
        }}
      ></div>
      {message && (
        <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>
          {message}
        </span>
      )}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default Loading;
