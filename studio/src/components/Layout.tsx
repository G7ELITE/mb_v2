
import { useState } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { 
  HomeIcon, 
  CogIcon, 
  PlayIcon, 
  DocumentTextIcon,
  BoltIcon,
  CloudArrowUpIcon,
  UsersIcon,
  SunIcon,
  MoonIcon,
  Bars3Icon,
  ChevronLeftIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Leads', href: '/leads', icon: UsersIcon },
  { name: 'Procedimentos', href: '/procedures', icon: DocumentTextIcon },
  { name: 'Automações', href: '/automations', icon: BoltIcon },
  { name: 'Intake & Âncoras', href: '/intake', icon: CogIcon },
  { name: 'Simulador', href: '/simulator', icon: PlayIcon },
  { name: 'Publicação', href: '/publish', icon: CloudArrowUpIcon },
];

export default function Layout() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-white dark:bg-gray-800 shadow-sm border-r border-gray-200 dark:border-gray-700 transition-all duration-300 relative`}>
        {/* Header da sidebar */}
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">MB</span>
              </div>
              {!sidebarCollapsed && (
                <span className="ml-3 text-lg font-bold text-gray-900 dark:text-white">MB Studio</span>
              )}
            </div>
            
            {/* Toggle button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {sidebarCollapsed ? (
                <Bars3Icon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              ) : (
                <ChevronLeftIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              )}
            </button>
          </div>
        </div>

        <nav className="px-2 pb-4">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = item.href === '/' 
                ? location.pathname === '/'
                : location.pathname.startsWith(item.href);
              
              return (
                <div key={item.name} className="relative group">
                  <Link
                    to={item.href}
                    className={`sidebar-nav-item ${isActive ? 'active' : ''} ${
                      sidebarCollapsed ? 'justify-center px-3 py-3' : ''
                    }`}
                  >
                    <item.icon className={`h-5 w-5 ${sidebarCollapsed ? '' : 'mr-3'}`} />
                    {!sidebarCollapsed && <span>{item.name}</span>}
                  </Link>
                  
                  {/* Tooltip quando colapsada */}
                  {sidebarCollapsed && (
                    <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                      {item.name}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </nav>

        {/* Footer da sidebar */}
        <div className={`absolute bottom-0 left-0 ${sidebarCollapsed ? 'w-16' : 'w-64'} p-4 border-t border-gray-200 dark:border-gray-700 transition-all duration-300`}>
          <div className="space-y-3">
            {/* Toggle de tema */}
            <div className="relative group">
              <button
                onClick={toggleTheme}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors ${
                  sidebarCollapsed ? 'justify-center' : ''
                }`}
              >
                {theme === 'light' ? (
                  <>
                    <MoonIcon className="h-4 w-4" />
                    {!sidebarCollapsed && <span>Modo escuro</span>}
                  </>
                ) : (
                  <>
                    <SunIcon className="h-4 w-4" />
                    {!sidebarCollapsed && <span>Modo claro</span>}
                  </>
                )}
              </button>
              
              {/* Tooltip para tema quando colapsada */}
              {sidebarCollapsed && (
                <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                  {theme === 'light' ? 'Modo escuro' : 'Modo claro'}
                </div>
              )}
            </div>
            
            {!sidebarCollapsed && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                  Backend conectado
                </div>
                <div className="mt-1">Modo: Desenvolvimento</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
