import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tokenService } from '../services/token.service';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { KeyIcon, PlusIcon, TrashIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import type { TokenGenerationResponse } from '../types/token';

const tokenSchema = z.object({
  name: z.string().min(1, 'Token name is required').max(50, 'Name must be 50 characters or less'),
});

type TokenFormData = z.infer<typeof tokenSchema>;

export const TokensPage = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTokenResponse, setNewTokenResponse] = useState<TokenGenerationResponse | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);

  const { data: tokens, isLoading } = useQuery({
    queryKey: ['tokens'],
    queryFn: tokenService.getTokens,
  });

  const createTokenMutation = useMutation({
    mutationFn: tokenService.createToken,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] });
      setNewTokenResponse(data);
    },
  });

  const revokeTokenMutation = useMutation({
    mutationFn: tokenService.revokeToken,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] });
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TokenFormData>({
    resolver: zodResolver(tokenSchema),
  });

  const onSubmit = async (data: TokenFormData) => {
    await createTokenMutation.mutateAsync(data);
    reset();
  };

  const handleCopyToken = () => {
    if (newTokenResponse) {
      navigator.clipboard.writeText(newTokenResponse.tokenOnce);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setNewTokenResponse(null);
    reset();
  };

  const handleRevokeToken = async (tokenId: string) => {
    if (confirm('Are you sure you want to revoke this token? This action cannot be undone.')) {
      await revokeTokenMutation.mutateAsync(tokenId);
    }
  };

  const activeTokens = tokens?.filter((t) => !t.revokedAt) || [];
  const revokedTokens = tokens?.filter((t) => t.revokedAt) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">API Tokens</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your API authentication tokens
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Token
        </button>
      </div>

      {/* Active Tokens */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Active Tokens ({activeTokens.length})
        </h2>
        <div className="grid gap-4">
          {activeTokens.length === 0 ? (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-8 text-center">
              <KeyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No active tokens</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Create your first API token to get started
              </p>
            </div>
          ) : (
            activeTokens.map((token) => (
              <div
                key={token.id}
                className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <KeyIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {token.name}
                      </h3>
                      <span className="ml-3 px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded text-sm font-mono">
                        {token.tokenPrefix}...
                      </span>
                    </div>
                    <div className="mt-2 flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-500">
                      <span>Created {format(new Date(token.createdAt), 'PPP')}</span>
                      {token.lastUsedAt && (
                        <span>Last used {format(new Date(token.lastUsedAt), 'PPP')}</span>
                      )}
                      {!token.lastUsedAt && <span>Never used</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRevokeToken(token.id)}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Revoked Tokens */}
      {revokedTokens.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Revoked Tokens ({revokedTokens.length})
          </h2>
          <div className="grid gap-4">
            {revokedTokens.map((token) => (
              <div
                key={token.id}
                className="bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-800 p-6 opacity-60"
              >
                <div className="flex items-center">
                  <KeyIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 line-through">
                    {token.name}
                  </h3>
                  <span className="ml-3 px-2 py-1 bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded text-sm">
                    Revoked
                  </span>
                </div>
                <div className="mt-2 text-sm text-gray-500 dark:text-gray-500">
                  Revoked on {format(new Date(token.revokedAt!), 'PPP')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Token Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl w-full max-w-md">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                {newTokenResponse ? 'Token Created Successfully' : 'Create New Token'}
              </h2>

              {!newTokenResponse ? (
                <form onSubmit={handleSubmit(onSubmit)}>
                  <div className="mb-4">
                    <label
                      htmlFor="name"
                      className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >
                      Token Name
                    </label>
                    <input
                      {...register('name')}
                      type="text"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
                      placeholder="e.g., Production API Key"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                        {errors.name.message}
                      </p>
                    )}
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {isSubmitting ? 'Creating...' : 'Create Token'}
                    </button>
                  </div>
                </form>
              ) : (
                <div>
                  <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      Make sure to copy your token now. You won't be able to see it again!
                    </p>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Your API Token
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={newTokenResponse.tokenOnce}
                        readOnly
                        className="flex-1 px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg font-mono text-sm"
                      />
                      <button
                        onClick={handleCopyToken}
                        className={clsx(
                          'p-2 rounded-lg transition-colors',
                          copiedToken
                            ? 'bg-green-100 text-green-600 dark:bg-green-900/20 dark:text-green-400'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
                        )}
                      >
                        <ClipboardDocumentIcon className="h-5 w-5" />
                      </button>
                    </div>
                    {copiedToken && (
                      <p className="text-sm text-green-600 dark:text-green-400 mt-2">
                        Token copied to clipboard!
                      </p>
                    )}
                  </div>

                  <div className="flex justify-end">
                    <button
                      onClick={handleCloseModal}
                      className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
                    >
                      Done
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
