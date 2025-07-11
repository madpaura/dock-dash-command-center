
import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Container, 
  Activity, 
  FileText, 
  BarChart3
} from 'lucide-react';

const navItems = [
  { path: '/user', label: 'Dashboard', icon: BarChart3, exact: true },
  { path: '/user/containers', label: 'My Containers', icon: Container },
  { path: '/user/monitoring', label: 'Resource Usage', icon: Activity },
  { path: '/user/logs', label: 'Application Logs', icon: FileText },
];

export const UserSidebar: React.FC = () => {
  return (
    <aside className="fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] bg-slate-900/95 backdrop-blur-sm border-r border-slate-700 overflow-y-auto">
      <nav className="p-4 space-y-2">
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
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
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border border-blue-500/30' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
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
