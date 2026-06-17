'use client';

import { useState } from 'react';
import { Session } from '@/lib/types';
import { createSession, uploadFile } from '@/lib/api';

interface SidebarProps {
  sessions: Session[];
  selectedSession: Session | null;
  onSessionSelect: (session: Session) => void;
  onSessionCreated: (session: Session) => void;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export default function Sidebar({
  sessions,
  selectedSession,
  onSessionSelect,
  onSessionCreated,
  loading,
  error,
  onRefresh,
}: SidebarProps) {
  const [newSessionName, setNewSessionName] = useState<string>('');
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState<boolean>(false);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSessionName.trim()) return;

    try {
      setCreateLoading(true);
      const session = await createSession(newSessionName.trim());
      onSessionCreated(session);
      setNewSessionName('');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create session');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedSession || !e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];
    try {
      setUploading(true);
      setUploadError(null);
      await uploadFile(selectedSession.id, file);
      alert('File uploaded successfully');
      onRefresh();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Sessions</h2>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <form onSubmit={handleCreateSession} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            placeholder="New session name"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={createLoading}
          />
          <button
            type="submit"
            disabled={createLoading || !newSessionName.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createLoading ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {uploadError && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {uploadError}
        </div>
      )}

      <div className="mb-6">
        <h3 className="font-medium text-gray-700 mb-2">Upload Document</h3>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
          <input
            type="file"
            id="file-upload"
            onChange={handleFileUpload}
            disabled={!selectedSession || uploading}
            className="hidden"
          />
          <label
            htmlFor="file-upload"
            className={`cursor-pointer block ${(!selectedSession || uploading) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="text-gray-600">
              {uploading ? (
                <span>Uploading...</span>
              ) : selectedSession ? (
                <span>Click to upload PDF, Excel, or text files</span>
              ) : (
                <span>Select a session to upload files</span>
              )}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Supports .pdf, .xlsx, .txt, .docx
            </div>
          </label>
        </div>
      </div>

      <div>
        <h3 className="font-medium text-gray-700 mb-3">Your Sessions</h3>
        {loading ? (
          <div className="text-center py-4 text-gray-500">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-4 text-gray-500">No sessions yet. Create one above.</div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => onSessionSelect(session)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${selectedSession?.id === session.id ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 hover:bg-gray-100'}`}
              >
                <div className="font-medium text-gray-800">{session.name}</div>
                <div className="text-sm text-gray-500 mt-1">
                  Created: {new Date(session.created_at).toLocaleDateString()}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}