import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  UserCircleIcon,
  KeyIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

export const AccountPage = () => {
  const { user, logout } = useAuth();

  const accountSections = [
    {
      title: 'Profile Information',
      description: 'View your account details and verification status',
      icon: UserCircleIcon,
      items: [
        { label: 'Email', value: user?.email || 'Not available' },
        { label: 'User ID', value: user?.id || 'Not available' },
        {
          label: 'Email Verification',
          value: user?.isEmailVerified ? 'Verified' : 'Not Verified',
          status: user?.isEmailVerified ? 'success' : 'warning',
        },
        {
          label: 'Account Created',
          value: user?.dateJoined ? format(new Date(user.dateJoined), 'PPP') : 'Not available',
        },
      ],
    },
    {
      title: 'Security',
      description: 'Manage your account security settings',
      icon: ShieldCheckIcon,
      actions: [
        {
          title: 'Change Password',
          description: 'Update your account password',
          link: '/account/password',
          icon: KeyIcon,
        },
      ],
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
          Account Settings
        </h1>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-2">
          Manage your account information and security settings
        </p>
      </div>

      {/* Email Verification Banner */}
      {user && !user.isEmailVerified && (
        <div className="mb-4 sm:mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-3 sm:p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <ShieldCheckIcon className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-xs sm:text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Email verification required
              </h3>
              <p className="mt-1 text-xs sm:text-sm text-yellow-700 dark:text-yellow-300">
                Please verify your email address to access all features. Check your inbox for the
                verification email.
              </p>
              <Link
                to="/resend-verification"
                className="mt-2 inline-flex items-center text-xs sm:text-sm font-medium text-yellow-800 dark:text-yellow-200 hover:text-yellow-900 dark:hover:text-yellow-100"
              >
                Resend verification email
                <ArrowRightIcon className="ml-1 h-3 sm:h-4 w-3 sm:w-4" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Account Sections */}
      <div className="space-y-4 sm:space-y-6">
        {accountSections.map((section) => (
          <div
            key={section.title}
            className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
          >
            {/* Section Header */}
            <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center">
                <section.icon className="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
                <div className="min-w-0">
                  <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                    {section.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {section.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Section Content */}
            <div className="p-4 sm:p-6">
              {section.items && (
                <dl className="space-y-3 sm:space-y-4">
                  {section.items.map((item) => (
                    <div
                      key={item.label}
                      className="flex flex-col sm:flex-row sm:justify-between gap-1 sm:gap-2"
                    >
                      <dt className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400">
                        {item.label}
                      </dt>
                      <dd className="text-xs sm:text-sm text-gray-900 dark:text-white sm:text-right">
                        {item.status ? (
                          <span
                            className={`inline-flex items-center px-2 sm:px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              item.status === 'success'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                            }`}
                          >
                            {item.value}
                          </span>
                        ) : (
                          <span className="break-all">{item.value}</span>
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>
              )}

              {section.actions && (
                <div className="space-y-2 sm:space-y-3">
                  {section.actions.map((action) => (
                    <Link key={action.title} to={action.link} className="block group">
                      <div className="p-3 sm:p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center min-w-0">
                            <div className="flex-shrink-0">
                              <action.icon className="h-5 w-5 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400" />
                            </div>
                            <div className="ml-3 sm:ml-4 min-w-0">
                              <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white">
                                {action.title}
                              </p>
                              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                                {action.description}
                              </p>
                            </div>
                          </div>
                          <ArrowRightIcon className="h-4 sm:h-5 w-4 sm:w-5 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 flex-shrink-0" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Account Actions */}
      <div className="mt-6 sm:mt-8 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        {/* Section Header */}
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center">
            <ArrowRightOnRectangleIcon className="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
            <div className="min-w-0">
              <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                Account Actions
              </h2>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-1">
                Manage your session and account
              </p>
            </div>
          </div>
        </div>

        {/* Section Content */}
        <div className="p-4 sm:p-6">
          <button
            className="w-full sm:w-auto px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors text-xs sm:text-sm font-medium flex items-center justify-center sm:justify-start"
            onClick={() => logout()}
          >
            <ArrowRightOnRectangleIcon className="h-4 w-4 mr-2" />
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};
