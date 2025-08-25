import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  HomeIcon,
  KeyIcon,
  CreditCardIcon,
  ChartBarIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';
import clsx from 'clsx';
import { EmailVerificationBanner } from '../components/EmailVerificationBanner';

export const MainLayout = () => {
  const { user, logout } = useAuth();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'API Tokens', href: '/tokens', icon: KeyIcon },
    { name: 'Billing', href: '/billing', icon: CreditCardIcon },
    { name: 'Usage', href: '/usage', icon: ChartBarIcon },
    { name: 'Account', href: '/account', icon: UserCircleIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Email verification banner */}
      <EmailVerificationBanner />

      <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
        {/* Sidebar */}
        <div
          className={clsx(
            'bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300',
            isSidebarCollapsed ? 'w-16' : 'w-64'
          )}
        >
          <div className="flex flex-col h-full">
            {/* Logo/Brand */}
            <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800">
              <h1
                className={clsx(
                  'font-semibold text-xl text-gray-900 dark:text-white transition-opacity',
                  isSidebarCollapsed && 'opacity-0'
                )}
              >
                API Platform
              </h1>
              <button
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <svg
                  className="w-5 h-5 text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d={isSidebarCollapsed ? 'M13 5l7 7-7 7' : 'M11 19l-7-7 7-7'}
                  />
                </svg>
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-2 py-4 space-y-1">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                        : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    )
                  }
                  title={isSidebarCollapsed ? item.name : undefined}
                >
                  <item.icon
                    className={clsx(
                      'flex-shrink-0 h-5 w-5',
                      !isSidebarCollapsed && 'mr-3'
                    )}
                  />
                  {!isSidebarCollapsed && <span>{item.name}</span>}
                </NavLink>
              ))}
            </nav>

            {/* User section */}
            <div className="border-t border-gray-200 dark:border-gray-800 p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user?.email?.[0]?.toUpperCase() || 'U'}
                    </span>
                  </div>
                </div>
                {!isSidebarCollapsed && (
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
                      {user?.email}
                    </p>
                  </div>
                )}
                <button
                  onClick={handleLogout}
                  className={clsx(
                    'p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800',
                    isSidebarCollapsed ? 'ml-0' : 'ml-2'
                  )}
                  title="Logout"
                >
                  <ArrowRightOnRectangleIcon className="h-5 w-5 text-gray-500" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};
