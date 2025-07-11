
import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { AdminSidebar } from './AdminSidebar';
import { UserSidebar } from './UserSidebar';
import { Header } from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex">
        {user?.role === 'admin' ? <AdminSidebar /> : <UserSidebar />}
        <main className="flex-1 p-6 ml-64 mt-16">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
