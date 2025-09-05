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
  ChevronLeft,
  ChevronRight,
  Info
} from 'lucide-react';
import { useSidebar } from '../hooks/useSidebar';

const navItems = [
  { path: '/admin', label: 'Dashboard', icon: BarChart3, exact: true },
  { path: '/admin/servers', label: 'Servers', icon: HardDrive },
  { path: '/admin/containers', label: 'Containers', icon: Container },
  { path: '/admin/images', label: 'Images', icon: Image },
  { path: '/admin/users', label: 'Users', icon: Users },
  { path: '/admin/logs', label: 'Logs', icon: FileText },
  // { path: '/admin/monitoring', label: 'Monitoring', icon: Activity },
  // { path: '/admin/networks', label: 'Networks', icon: Network },
  // { path: '/admin/volumes', label: 'Volumes', icon: HardDrive },
];

export const AdminSidebar: React.FC = () => {
  const { collapsed, toggleCollapsed } = useSidebar();
  return (
    <aside className={`fixed left-0 top-16 ${collapsed ? 'w-16' : 'w-64'} h-[calc(100vh-4rem)] bg-sidebar backdrop-blur-sm border-r border-sidebar-border overflow-y-auto transition-all duration-300 flex flex-col`}>
      <div className="flex justify-end p-2">
        <button 
          onClick={toggleCollapsed}
          className="p-1.5 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-primary transition-colors"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="p-4 space-y-2 flex-1">
        {!collapsed && (
          <div className="mb-6">
            <h3 className="text-xs font-medium text-sidebar-foreground uppercase tracking-wider mb-3">
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
            {!collapsed && <span className="font-normal">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* About Banner */}
      <div className="p-4 border-t border-sidebar-border">
        {collapsed ? (
          <div className="flex justify-center">
            <div 
              className="p-2 rounded-lg bg-sidebar-accent/30 text-sidebar-foreground hover:bg-sidebar-accent/50 transition-colors cursor-pointer"
              title="About GPU Dashboard"
            >
              <Info className="w-6 h-6" />
            </div>
          </div>
        ) : (
          <div className="bg-sidebar-accent/30 rounded-lg p-3 border border-sidebar-primary/20">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-sidebar-primary" />
              <span className="text-sm font-normal text-sidebar-foreground">About</span>
            </div>
            <div className="text-xs text-sidebar-foreground/70 leading-relaxed">
              <p className="mb-1">GPU Dashboard v1.0</p>
              <p className="mb-2">Built with React & Flask</p>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-black dark:bg-white flex items-center justify-center text-white dark:text-black text-xs font-bold hover:animate-spin hover:scale-110 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl">
                  V
                </div>
                <span className="hover:text-sidebar-primary transition-colors duration-200">by Vishwa (Using AI)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
