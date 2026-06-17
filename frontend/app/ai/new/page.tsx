'use client';

import { useState } from 'react';
import { createSession } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function NewAiSessionPage() {
  const router = useRouter();
  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Session name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const session = await createSession(name.trim());
      router.push(`/?session=${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create New AI Session</h1>
        <p className="text-gray-600 mt-2">
          Create a new session to upload and analyze documents with AI
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">
              <div className="font-medium">Error</div>
              <div className="text-sm mt-1">{error}</div>
            </div>
          )}

          <div className="mb-6">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Session Name *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Quarterly Reports Analysis"
              required
              disabled={loading}
            />
            <p className="mt-2 text-sm text-gray-500">
              Choose a descriptive name for your session
            </p>
          </div>

          <div className="mb-8">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe what this session will be used for..."
              disabled={loading}
            />
            <p className="mt-2 text-sm text-gray-500">
              Add any notes or context about this session
            </p>
          </div>

          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </span>
              ) : (
                'Create Session'
              )}
            </button>
          </div>
        </form>
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">What happens next?</h3>
        <ul className="space-y-2 text-blue-800">
          <li className="flex items-start">
            <div className="mr-2 mt-1">1.</div>
            <div>After creating the session, you'll be redirected to the main interface</div>
          </li>
          <li className="flex items-start">
            <div className="mr-2 mt-1">2.</div>
            <div>Upload documents (PDF, Excel, text files) to your new session</div>
          </li>
          <li className="flex items-start">
            <div className="mr-2 mt-1">3.</div>
            <div>Ingest the documents to make them searchable by AI</div>
          </li>
          <li className="flex items-start">
            <div className="mr-2 mt-1">4.</div>
            <div>Start asking questions about your documents using the chat interface</div>
          </li>
        </ul>
      </div>
    </div>
  );
}