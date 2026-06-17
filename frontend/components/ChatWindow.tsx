'use client';

import { useState, useRef, useEffect } from 'react';
import { Session, QueryResponse, Citation } from '@/lib/types';
import { aiQuery, ingestDocuments } from '@/lib/api';

interface ChatWindowProps {
  selectedSession: Session | null;
  onSessionRefresh: () => void;
}

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  citations?: Citation[];
  timestamp: Date;
}

export default function ChatWindow({ selectedSession, onSessionRefresh }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [ingesting, setIngesting] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !selectedSession || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response: QueryResponse = await aiQuery(selectedSession.id, currentInput);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.answer,
        isUser: false,
        citations: response.citations,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get AI response');
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your query.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleIngestDocuments = async () => {
    if (!selectedSession) return;

    try {
      setIngesting(true);
      setError(null);
      await ingestDocuments(selectedSession.id, []);
      alert('Documents ingested successfully! You can now query them.');
      onSessionRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to ingest documents');
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">
              {selectedSession ? selectedSession.name : 'Chat'}
            </h2>
            {selectedSession && (
              <p className="text-sm text-gray-600 mt-1">
                Session ID: {selectedSession.id.slice(0, 8)}...
              </p>
            )}
          </div>
          {selectedSession && (
            <button
              onClick={handleIngestDocuments}
              disabled={ingesting}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {ingesting ? 'Ingesting...' : 'Ingest Documents'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        {!selectedSession ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-4xl mb-4">🤖</div>
              <p className="text-lg">Select a session to start chatting</p>
              <p className="text-sm mt-2">Or create a new session from the sidebar</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-4xl mb-4">💬</div>
              <p className="text-lg">Start a conversation with your documents</p>
              <p className="text-sm mt-2">Ask questions about your uploaded files</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-lg p-4 ${message.isUser ? 'bg-blue-100' : 'bg-gray-100'}`}
                >
                  <div className="flex items-center mb-2">
                    <div className={`w-2 h-2 rounded-full mr-2 ${message.isUser ? 'bg-blue-500' : 'bg-gray-500'}`} />
                    <span className="text-sm font-medium">
                      {message.isUser ? 'You' : 'AI Assistant'}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="text-gray-800 whitespace-pre-wrap">{message.content}</div>
                  
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-300">
                      <div className="text-sm font-medium text-gray-700 mb-2">Sources:</div>
                      <div className="space-y-2">
                        {message.citations.map((citation, index) => (
                          <div key={index} className="text-sm bg-white p-3 rounded border border-gray-200">
                            <div className="font-medium text-gray-800">{citation.source}</div>
                            <div className="text-gray-600 mt-1">{citation.text}</div>
                            {citation.page && (
                              <div className="text-xs text-gray-500 mt-1">Page {citation.page}</div>
                            )}
                            <div className="text-xs text-gray-500 mt-1">
                              Confidence: {(citation.confidence * 100).toFixed(1)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="max-w-3xl rounded-lg p-4 bg-gray-100">
                  <div className="flex items-center">
                    <div className="w-2 h-2 rounded-full mr-2 bg-gray-500" />
                    <span className="text-sm font-medium">AI Assistant</span>
                  </div>
                  <div className="flex items-center mt-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce mr-1" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce mr-1 delay-75" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {selectedSession && (
        <form onSubmit={handleSendMessage} className="p-6 border-t border-gray-200">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            Press Enter to send. The AI will search through your uploaded documents.
          </div>
        </form>
      )}
    </div>
  );
}