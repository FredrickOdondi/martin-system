import { CommandAutocompleteResult } from '../../types/agent';

interface CommandAutocompleteProps {
  suggestions: CommandAutocompleteResult[];
  selectedIndex: number;
  onSelect: (suggestion: CommandAutocompleteResult) => void;
  onHover: (index: number) => void;
}

/**
 * Command Autocomplete Dropdown
 *
 * Shows slash command suggestions as user types.
 * Displays command, description, and example.
 */
export function CommandAutocomplete({
  suggestions,
  selectedIndex,
  onSelect,
  onHover
}: CommandAutocompleteProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="absolute bottom-full left-0 mb-2 w-72 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden transform transition-all">
      <div className="max-h-64 overflow-y-auto py-1">
        {suggestions.map((suggestion, index) => (
          <button
            key={suggestion.command}
            onClick={() => onSelect(suggestion)}
            onMouseEnter={() => onHover(index)}
            className={`w-full text-left px-3 py-2.5 transition-colors flex items-center gap-3 ${index === selectedIndex
                ? 'bg-blue-50 dark:bg-blue-900/40'
                : 'hover:bg-gray-50 dark:hover:bg-slate-800'
              }`}
          >
            {/* Icon */}
            <div className={`size-8 rounded-md flex items-center justify-center flex-shrink-0 ${index === selectedIndex
                ? 'bg-blue-100 dark:bg-blue-800 text-blue-600 dark:text-blue-200'
                : 'bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400'
              }`}>
              <span className="material-symbols-outlined text-[18px]">
                {getCategoryIcon(suggestion.category || 'general')}
              </span>
            </div>

            {/* Info */}
            <div className="min-w-0 flex-1">
              <div className={`text-sm font-medium font-mono ${index === selectedIndex
                  ? 'text-blue-700 dark:text-blue-100'
                  : 'text-gray-900 dark:text-gray-100'
                }`}>
                {suggestion.command}
              </div>
              <div className={`text-xs truncate ${index === selectedIndex
                  ? 'text-blue-600/80 dark:text-blue-300/80'
                  : 'text-gray-500 dark:text-gray-400'
                }`}>
                {suggestion.description}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    communication: 'email',
    documents: 'description',
    meetings: 'event',
    analysis: 'analytics',
    general: 'terminal'
  };
  return icons[category] || 'terminal';
}

export default CommandAutocomplete;
