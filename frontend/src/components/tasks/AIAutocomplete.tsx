import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

interface AIAutocompleteProps {
  value: string;
  onSelect: (suggestion: string) => void;
}

const AIAutocomplete: React.FC<AIAutocompleteProps> = ({ value, onSelect }) => {
  const [suggestion, setSuggestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (value.length < 3) {
      setSuggestion('');
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(
          `http://localhost:8000/api/v1/ai/suggest?prefix=${encodeURIComponent(value)}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.suggestion) {
            setSuggestion(data.suggestion);
          }
        }
      } catch (error) {
        console.error('AI autocomplete error:', error);
      } finally {
        setIsLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [value]);

  if (!suggestion || isLoading) {
    return null;
  }

  return (
    <div className="mt-2 p-3 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
      <div className="flex items-start gap-2">
        <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-xs font-medium text-purple-900 mb-1">AI Suggestion</p>
          <button
            onClick={() => onSelect(value + suggestion)}
            className="text-sm text-gray-700 hover:text-gray-900 text-left"
          >
            {value}<span className="text-purple-600 font-medium">{suggestion}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIAutocomplete;