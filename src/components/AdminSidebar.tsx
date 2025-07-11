import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Container, 
  Image, 
  Activity, 
  Users, 
  FileText, 
  Network, 
  HardDrive,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useSidebar } from '../hooks/useSidebar';

const navItems = [
  { path: '/admin', label: 'Dashboard', icon: BarChart3, exact: true },
  { path: '/admin/containers', label: 'Containers', icon: Container },
  { path: '/admin/images', label: 'Images', icon: Image },
  { path: '/admin/monitoring', label: 'Monitoring', icon: Activity },
  { path: '/admin/users', label: 'Users', icon: Users },
  { path: '/admin/logs', label: 'Logs', icon: FileText },
  { path: '/admin/networks', label: 'Networks', icon: Network },
  { path: '/admin/volumes', label: 'Volumes', icon: HardDrive },
  { path: '/admin/settings', label: 'Settings', icon: Settings },
];

export const AdminSidebar: React.FC = () => {
  const { collapsed, toggleCollapsed } = useSidebar();
  return (
    <aside className={`fixed left-0 top-16 ${collapsed ? 'w-16' : 'w-64'} h-[calc(100vh-4rem)] bg-sidebar backdrop-blur-sm border-r border-sidebar-border overflow-y-auto transition-all duration-300`}>
      <div className="flex justify-end p-2">
        <button 
          onClick={toggleCollapsed}
          className="p-1.5 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-primary transition-colors"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="p-4 space-y-2">
        {!collapsed && (
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-sidebar-foreground uppercase tracking-wider mb-3">
              Admin Panel
            </h3>
          </div>
        )}
        
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.exact}
            title={collapsed ? item.label : ''}
            className={({ isActive }) => 
              `flex ${collapsed ? 'justify-center' : 'items-center gap-3'} ${collapsed ? 'p-2' : 'px-3 py-2'} rounded-lg transition-all duration-200 ${
                isActive 
                  ? 'bg-sidebar-accent text-sidebar-primary border border-sidebar-primary/30' 
                  : 'text-sidebar-foreground hover:text-sidebar-primary-foreground hover:bg-sidebar-accent/50'
              }`
            }
          >
            <item.icon className={collapsed ? "w-10 h-10" : "w-6 h-6"} />
            {!collapsed && <span className="font-medium">{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};
