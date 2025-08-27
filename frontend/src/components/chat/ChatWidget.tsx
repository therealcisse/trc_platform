import { useState, useRef, useCallback, useEffect } from 'react';
import {
  ChatBubbleOvalLeftEllipsisIcon,
  XMarkIcon,
  PaperAirplaneIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline';
import { AnimatePresence, motion } from 'framer-motion';
import clsx from 'clsx';
import { testSolveService } from '../../services/testSolve.service';
import { useAuth } from '../../contexts/AuthContext';

interface Message {
  id: string;
  type: 'user' | 'system' | 'error';
  content: string;
  imageUrl?: string;
  timestamp: Date;
  isLoading?: boolean;
}

export const ChatWidget = () => {
  const { user, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Don't render if user is not authenticated or email not verified
  if (!isAuthenticated || !user?.isEmailVerified) {
    return null;
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'error',
        content: 'Please select a valid image file',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'error',
        content: 'Image size must be less than 10MB',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    setSelectedImage(file);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSend = async () => {
    if (!selectedImage || isProcessing) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: 'Solve this problem:',
      imageUrl: imagePreview || undefined,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add loading message
    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'system',
      content: 'Processing your image...',
      timestamp: new Date(),
      isLoading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);

    // Clear selected image
    const imageToProcess = selectedImage;
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    setIsProcessing(true);

    try {
      const response = await testSolveService.solveImage(imageToProcess);

      // Remove loading message and add result
      setMessages((prev) => {
        const filtered = prev.filter((m) => !m.isLoading);
        const resultMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: 'system',
          content: response.result,
          timestamp: new Date(),
        };
        return [...filtered, resultMessage];
      });
    } catch (error: any) {
      // Remove loading message and add error
      setMessages((prev) => {
        const filtered = prev.filter((m) => !m.isLoading);
        const errorMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: 'error',
          content: error.response?.data?.detail || 'Failed to process image. Please try again.',
          timestamp: new Date(),
        };
        return [...filtered, errorMessage];
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    // Clear messages after closing
    setTimeout(() => {
      setMessages([]);
      setSelectedImage(null);
      setImagePreview(null);
    }, 300);
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      // Simulate file input change
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files;
        const event = new Event('change', { bubbles: true });
        fileInputRef.current.dispatchEvent(event);
      }
    }
  }, []);

  return (
    <>
      {/* Floating Action Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 bg-primary-600 hover:bg-primary-700 text-white rounded-full p-4 shadow-lg transition-colors"
            aria-label="Open chat"
          >
            <ChatBubbleOvalLeftEllipsisIcon className="h-6 w-6" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Dialog */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={clsx(
              'fixed z-50 bg-white dark:bg-gray-900 shadow-2xl',
              'bottom-0 right-0 md:bottom-6 md:right-6',
              'w-full md:w-96 h-[100vh] md:h-[600px] md:rounded-2xl',
              'flex flex-col overflow-hidden'
            )}
          >
            {/* Header */}
            <div className="bg-primary-600 text-white p-4 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg">Test Image Solver</h3>
                <p className="text-sm text-primary-100">Try out the API</p>
              </div>
              <button
                onClick={handleClose}
                className="p-2 hover:bg-primary-700 rounded-lg transition-colors"
                aria-label="Close chat"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Messages Area */}
            <div
              className="flex-1 overflow-y-auto p-4 space-y-4"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                  <PhotoIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-sm">Upload an image to get started</p>
                  <p className="text-xs mt-2">Drag and drop or click to select</p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={clsx(
                      'flex',
                      message.type === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={clsx(
                        'max-w-[80%] rounded-lg p-3',
                        message.type === 'user'
                          ? 'bg-primary-600 text-white'
                          : message.type === 'error'
                            ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                      )}
                    >
                      {message.imageUrl && (
                        <img
                          src={message.imageUrl}
                          alt="User upload"
                          className="rounded-lg mb-2 max-w-full"
                        />
                      )}
                      {message.isLoading ? (
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 dark:border-primary-400"></div>
                          <span className="text-sm">{message.content}</span>
                        </div>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
                      )}
                      <p className="text-xs mt-1 opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4">
              {imagePreview && (
                <div className="mb-3 relative">
                  <img
                    src={imagePreview}
                    alt="Selected"
                    className="h-20 w-20 object-cover rounded-lg"
                  />
                  <button
                    onClick={() => {
                      setSelectedImage(null);
                      setImagePreview(null);
                      if (fileInputRef.current) {
                        fileInputRef.current.value = '';
                      }
                    }}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                    aria-label="Remove image"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                  id="chat-file-input"
                />
                <label
                  htmlFor="chat-file-input"
                  className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors cursor-pointer"
                >
                  <PhotoIcon className="h-5 w-5" />
                </label>

                <button
                  onClick={handleSend}
                  disabled={!selectedImage || isProcessing}
                  className={clsx(
                    'flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg transition-colors',
                    selectedImage && !isProcessing
                      ? 'bg-primary-600 hover:bg-primary-700 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                  )}
                >
                  <span>{isProcessing ? 'Processing...' : 'Send Image'}</span>
                  {!isProcessing && <PaperAirplaneIcon className="h-4 w-4" />}
                </button>
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                Test requests count towards your usage
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
