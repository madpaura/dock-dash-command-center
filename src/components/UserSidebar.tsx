import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Container, 
  Activity, 
  FileText, 
  BarChart3,
  FolderOpen
} from 'lucide-react';

const navItems = [
  { path: '/user', label: 'Dashboard', icon: BarChart3, exact: true },
  { path: '/user/containers', label: 'My Containers', icon: Container },
  { path: '/user/files', label: 'File Manager', icon: FolderOpen },
  { path: '/user/monitoring', label: 'Resource Usage', icon: Activity },
  { path: '/user/logs', label: 'Application Logs', icon: FileText },
];

export const UserSidebar: React.FC = () => {
  return (
    <aside className="fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] bg-sidebar backdrop-blur-sm border-r border-sidebar-border overflow-y-auto">
      <nav className="p-4 space-y-2">
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-sidebar-foreground uppercase tracking-wider mb-3">
            User Panel
          </h3>
        </div>
        
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.exact}
            className={({ isActive }) => 
              `flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                isActive 
                  ? 'bg-sidebar-accent text-sidebar-primary border border-sidebar-primary/30' 
                  : 'text-sidebar-foreground hover:text-sidebar-primary-foreground hover:bg-sidebar-accent/50'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};
