import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ThemeProvider } from './hooks/useTheme';
import { Layout } from './components/Layout';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { LoadingScreen } from './components/LoadingScreen';
import { AdminDashboard } from './pages/AdminDashboard';
import { AdminServers } from './pages/AdminServers';
import { AdminUsers } from './pages/AdminUsers';
import { AdminLogs } from './pages/AdminLogs';
import { AdminImages } from './pages/AdminImages';
import { UserDashboard } from './pages/UserDashboard';
import { UserContainers } from './pages/UserContainers';
import { UserFileBrowser } from './pages/UserFileBrowser';

const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredRole?: 'admin' | 'user' }> = ({ 
  children, 
  requiredRole 
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to={user?.role === 'admin' ? '/admin' : '/user'} replace />;
  }

  return <Layout>{children}</Layout>;
};

const AppRoutes: React.FC = () => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to={user?.role === 'admin' ? '/admin' : '/user'} replace />} />
      <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to={user?.role === 'admin' ? '/admin' : '/user'} replace />} />
      <Route path="/" element={<Navigate to={isAuthenticated ? (user?.role === 'admin' ? '/admin' : '/user') : '/login'} replace />} />
      
      {/* Admin Routes */}
      <Route path="/admin" element={
        <ProtectedRoute requiredRole="admin">
          <AdminDashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/admin/servers" element={
        <ProtectedRoute requiredRole="admin">
          <AdminServers />
        </ProtectedRoute>
      } />
      
      <Route path="/admin/users" element={
        <ProtectedRoute requiredRole="admin">
          <AdminUsers />
        </ProtectedRoute>
      } />
      
      <Route path="/admin/logs" element={
        <ProtectedRoute requiredRole="admin">
          <AdminLogs />
        </ProtectedRoute>
      } />
      
      <Route path="/admin/images" element={
        <ProtectedRoute requiredRole="admin">
          <AdminImages />
        </ProtectedRoute>
      } />
      
      {/* User Routes */}
      <Route path="/user" element={
        <ProtectedRoute requiredRole="user">
          <UserDashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/user/containers" element={
        <ProtectedRoute requiredRole="user">
          <UserContainers />
        </ProtectedRoute>
      } /> 
      
      <Route path="/user/files" element={
        <ProtectedRoute requiredRole="user">
          <UserFileBrowser />
        </ProtectedRoute>
      } />
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to={user?.role === 'admin' ? '/admin' : '/user'} replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
