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
  ChevronLeftIcon,
  CpuChipIcon,
  UserGroupIcon,
  Square3Stack3DIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Leads', href: '/leads', icon: UsersIcon },
  { name: 'Procedimentos', href: '/procedures', icon: DocumentTextIcon },
  { name: 'Automações', href: '/automations', icon: BoltIcon },
  { name: 'Intake & Âncoras', href: '/intake', icon: CogIcon },
  { name: 'RAG', href: '/rag', icon: CpuChipIcon },
  { name: 'Equipe', href: '/equipe', icon: UserGroupIcon },
  { name: 'Equipe - Consultas', href: '/equipe-consultas', icon: Square3Stack3DIcon },
  { name: 'Simulador', href: '/simulator', icon: PlayIcon },
  { name: 'Publicação', href: '/publish', icon: CloudArrowUpIcon },
];

interface EquipeLayoutProps {
  showSidebar: boolean;
  children?: React.ReactNode;
}

export default function EquipeLayout({ showSidebar, children }: EquipeLayoutProps) {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar - Condicional baseado em showSidebar */}
      {showSidebar && (
        <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-white dark:bg-gray-800 shadow-sm border-r border-gray-200 dark:border-gray-700 transition-all duration-300 relative`}>
          {/* Header da sidebar */}
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">MB</span>
                </div>
                {!sidebarCollapsed && (
                  <span className="ml-2 text-lg font-semibold text-gray-900 dark:text-white">ManyBlack</span>
                )}
              </div>
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-1.5 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
              >
                {sidebarCollapsed ? <Bars3Icon className="w-5 h-5" /> : <ChevronLeftIcon className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="mt-8 px-4">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <li key={item.name}>
                    <Link
                      to={item.href}
                      className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                          : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-700'
                      }`}
                      title={sidebarCollapsed ? item.name : ''}
                    >
                      <item.icon
                        className={`${sidebarCollapsed ? 'mr-0' : 'mr-3'} flex-shrink-0 h-5 w-5 transition-colors ${
                          isActive 
                            ? 'text-blue-500 dark:text-blue-300' 
                            : 'text-gray-400 group-hover:text-gray-500 dark:text-gray-400 dark:group-hover:text-gray-300'
                        }`}
                      />
                      {!sidebarCollapsed && item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Theme Toggle */}
          {!sidebarCollapsed && (
            <div className="absolute bottom-4 left-4 right-4">
              <button
                onClick={toggleTheme}
                className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 dark:text-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
              >
                {theme === 'light' ? (
                  <>
                    <MoonIcon className="w-4 h-4 mr-2" />
                    Modo Escuro
                  </>
                ) : (
                  <>
                    <SunIcon className="w-4 h-4 mr-2" />
                    Modo Claro
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - apenas quando showSidebar = true (modo Admin) */}
        {showSidebar && (
          <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
            <div className="px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  {/* Conteúdo do header quando necessário */}
                </div>
                <div className="flex items-center">
                  {/* Espaço para controles adicionais se necessário */}
                </div>
              </div>
            </div>
          </header>
        )}

        {/* Page Content - ocupa tela toda quando showSidebar = false */}
        <main className={showSidebar ? "flex-1 overflow-y-auto" : "min-h-screen overflow-y-auto"}>
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
}
