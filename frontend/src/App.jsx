import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './components/common/Toast';
import ProtectedRoute from './components/common/ProtectedRoute';
import Navbar from './components/common/Navbar';
import Login from './components/Login/Login';
import Dashboard from './components/Dashboard/Dashboard';
import TuitionPayment from './components/TuitionPayment/TuitionPayment';
import TransactionHistory from './components/TransactionHistory/TransactionHistory';

// Main layout wrapper for protected dashboard pages (with Navbar and responsive container)
const DashboardLayout = ({ children }) => (
  <div className="app-container">
    <Navbar />
    <main className="main-content">
      {children}
    </main>
  </div>
);

function App() {
  return (
    <Router>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Standalone full-screen Login Page (No white frame around) */}
            <Route path="/login" element={<Login />} />

            {/* Protected Dashboard Pages */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Dashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/payment"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <TuitionPayment />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <TransactionHistory />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
