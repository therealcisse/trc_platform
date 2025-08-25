import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  UserCircleIcon, 
  KeyIcon, 
  ShieldCheckIcon,
  ArrowRightIcon 
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
          value: user?.emailVerified ? 'Verified' : 'Not Verified',
          status: user?.emailVerified ? 'success' : 'warning'
        },
        { 
          label: 'Account Created', 
          value: user?.createdAt ? format(new Date(user.createdAt), 'PPP') : 'Not available' 
        },
      ]
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
        }
      ]
    }
  ];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Account Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage your account information and security settings
        </p>
      </div>

      {/* Email Verification Banner */}
      {user && !user.emailVerified && (
        <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <ShieldCheckIcon className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Email verification required
              </h3>
              <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                Please verify your email address to access all features. Check your inbox for the verification email.
              </p>
              <Link
                to="/resend-verification"
                className="mt-2 inline-flex items-center text-sm font-medium text-yellow-800 dark:text-yellow-200 hover:text-yellow-900 dark:hover:text-yellow-100"
              >
                Resend verification email
                <ArrowRightIcon className="ml-1 h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Account Sections */}
      <div className="space-y-6">
        {accountSections.map((section) => (
          <div
            key={section.title}
            className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
          >
            {/* Section Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center">
                <section.icon className="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {section.title}
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {section.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Section Content */}
            <div className="p-6">
              {section.items && (
                <dl className="space-y-4">
                  {section.items.map((item) => (
                    <div key={item.label} className="flex justify-between">
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                        {item.label}
                      </dt>
                      <dd className="text-sm text-gray-900 dark:text-white">
                        {item.status ? (
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              item.status === 'success'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                            }`}
                          >
                            {item.value}
                          </span>
                        ) : (
                          item.value
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>
              )}

              {section.actions && (
                <div className="space-y-3">
                  {section.actions.map((action) => (
                    <Link
                      key={action.title}
                      to={action.link}
                      className="block group"
                    >
                      <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <action.icon className="h-5 w-5 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400" />
                            </div>
                            <div className="ml-4">
                              <p className="text-sm font-medium text-gray-900 dark:text-white">
                                {action.title}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {action.description}
                              </p>
                            </div>
                          </div>
                          <ArrowRightIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400" />
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

      {/* Danger Zone */}
      <div className="mt-8 bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-200 dark:border-red-900 p-6">
        <h3 className="text-lg font-semibold text-red-900 dark:text-red-400 mb-2">
          Danger Zone
        </h3>
        <p className="text-sm text-red-700 dark:text-red-300 mb-4">
          Actions in this section are permanent and cannot be undone.
        </p>
        <button
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
          onClick={() => logout()}
        >
          Logout from Account
        </button>
      </div>
    </div>
  );
};
