import { useState } from 'react';
import { Citation } from '../../services/agentService';
import { EmailApprovalRequest } from './EmailApprovalModal';

interface Message {
    id: string;
    role: 'user' | 'agent';
    content: string;
    timestamp: Date;
    citations?: Citation[];
    reactions?: MessageReaction[];
    agentName?: string;
    agentIcon?: string;
    approvalRequest?: EmailApprovalRequest;
    suggestions?: string[];
}

interface MessageReaction {
    emoji: string;
    count: number;
    users: string[];
}

interface EnhancedMessageBubbleProps {
    message: Message;
    onReact?: (messageId: string, emoji: string) => void;
    onCopy?: (content: string) => void;
    onReply?: (messageId: string) => void;
    onApprove?: (requestId: string) => void;
    onDecline?: (requestId: string) => void;
    onSuggestionClick?: (suggestion: string) => void;
}

// Function to parse and format markdown-like text with better styling
const formatMarkdownText = (text: string): JSX.Element => {
    const lines = text.split('\n');
    const elements: JSX.Element[] = [];

    let inCodeBlock = false;
    let codeBlockContent: string[] = [];

    lines.forEach((line, index) => {
        // Handle code blocks
        if (line.trim().startsWith('```')) {
            if (inCodeBlock) {
                // End code block
                elements.push(
                    <pre key={`code-${index}`} className="bg-slate-100 dark:bg-slate-800 rounded-lg p-3 my-2 overflow-x-auto">
                        <code className="text-xs font-mono text-slate-800 dark:text-slate-200">
                            {codeBlockContent.join('\n')}
                        </code>
                    </pre>
                );
                codeBlockContent = [];
                inCodeBlock = false;
            } else {
                inCodeBlock = true;
            }
            return;
        }

        if (inCodeBlock) {
            codeBlockContent.push(line);
            return;
        }

        // Format inline code
        let formattedLine = line.replace(/`([^`]+)`/g, '<code class="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-xs font-mono">$1</code>');

        // Format bold text
        formattedLine = formattedLine.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>');

        // Format italic text
        formattedLine = formattedLine.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');

        // Format links
        formattedLine = formattedLine.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>');

        // Handle headers
        if (/^\s*#{1,6}\s/.test(line)) {
            const match = line.match(/^\s*(#{1,6})/);
            const level = match ? match[1].length : 1;
            const content = line.replace(/^\s*#{1,6}\s/, '');

            let classes = '';
            switch (level) {
                case 1: classes = 'text-2xl font-bold mb-4 mt-6 border-b pb-2 border-slate-200 dark:border-slate-700'; break;
                case 2: classes = 'text-xl font-bold mb-3 mt-5 text-slate-900 dark:text-slate-100'; break;
                case 3: classes = 'text-lg font-bold mb-2 mt-4 text-slate-800 dark:text-slate-200'; break;
                case 4: classes = 'text-base font-bold mb-2 mt-3'; break;
                case 5: classes = 'text-sm font-bold mb-1 mt-2 uppercase tracking-wide text-slate-500 dark:text-slate-400'; break;
                default: classes = 'text-sm font-bold mb-1';
            }

            elements.push(
                <div key={`${index}-header`} className={classes} dangerouslySetInnerHTML={{ __html: content }}></div>
            );
            return;
        }

        // Handle numbered lists
        if (/^\d+\.\s/.test(line)) {
            const content = line.replace(/^\d+\.\s/, '');
            elements.push(
                <div key={index} className="mb-2 pl-4 flex items-start gap-2">
                    <span className="text-blue-600 dark:text-blue-400 font-semibold text-sm">•</span>
                    <span dangerouslySetInnerHTML={{ __html: content }}></span>
                </div>
            );
            return;
        }

        // Handle bullet points
        if (/^\s*[-*]\s/.test(line)) {
            const indent = line.search(/[-*]/);
            const content = line.replace(/^\s*[-*]\s/, '');
            elements.push(
                <div key={index} className="mb-1.5 flex items-start gap-2" style={{ paddingLeft: `${indent * 8}px` }}>
                    <span className="text-slate-400 text-sm mt-0.5">•</span>
                    <span dangerouslySetInnerHTML={{ __html: content }}></span>
                </div>
            );
            return;
        }

        // Empty lines
        if (line.trim() === '') {
            elements.push(<div key={index} className="h-2"></div>);
            return;
        }

        // Regular text
        elements.push(
            <div key={index} className="mb-1" dangerouslySetInnerHTML={{ __html: formattedLine }}></div>
        );
    });

    return <>{elements}</>;
};

export default function EnhancedMessageBubble({ message, onReact, onCopy, onReply, onApprove, onDecline, onSuggestionClick }: EnhancedMessageBubbleProps) {
    // Debug log to trace approval rendering
    if (message.approvalRequest) {
        console.log('[BUBBLE] Rendering bubble with approval request:', message.id, message.approvalRequest);
    }

    const [showActions, setShowActions] = useState(false);
    const [showReactions, setShowReactions] = useState(false);
    const [copied, setCopied] = useState(false);

    const commonReactions = ['👍', '❤️', '🎉', '🤔', '👀', '✅'];

    const handleCopy = () => {
        if (onCopy) {
            onCopy(message.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } else {
            navigator.clipboard.writeText(message.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleReact = (emoji: string) => {
        if (onReact) {
            onReact(message.id, emoji);
        }
        setShowReactions(false);
    };

    return (
        <div
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'} group animate-in fade-in slide-in-from-bottom-2 duration-300`}
            onMouseEnter={() => setShowActions(true)}
            onMouseLeave={() => {
                setShowActions(false);
                setShowReactions(false);
            }}
        >
            {message.role === 'agent' && (
                <div className="relative shrink-0">
                    <div className={`size-9 rounded-full ${message.agentIcon || 'bg-gradient-to-br from-blue-600 to-purple-600'} flex items-center justify-center text-white shadow-md`}>
                        <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                    </div>
                    {message.agentName && (
                        <div className="absolute -bottom-1 -right-1 size-4 rounded-full bg-green-500 border-2 border-white dark:border-[#0d121b] flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-[10px]">check</span>
                        </div>
                    )}
                </div>
            )}

            <div className="flex flex-col gap-1 max-w-[75%]">
                {/* Agent name tag for multi-agent responses */}
                {message.role === 'agent' && message.agentName && (
                    <div className="flex items-center gap-2 px-2">
                        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">{message.agentName}</span>
                        <span className="text-[10px] text-slate-400 dark:text-slate-500">AI Agent</span>
                    </div>
                )}

                <div className="relative">
                    {/* Message bubble */}
                    <div className={`${message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-lg'
                        : 'bg-white dark:bg-[#1a202c] shadow-md border border-[#e7ebf3] dark:border-[#2d3748]'
                        } rounded-2xl ${message.role === 'user' ? 'rounded-tr-sm' : 'rounded-tl-sm'} p-4 transition-all`}>
                        {/* Content */}
                        <div className={`text-sm leading-relaxed ${message.role === 'agent' ? 'text-[#0d121b] dark:text-white' : 'text-white'}`}>
                            {message.role === 'agent' ? formatMarkdownText(message.content) : message.content}
                        </div>

                        {/* Citations */}
                        {message.citations && message.citations.length > 0 && (
                            <div className="mt-4 pt-3 border-t border-[#e7ebf3] dark:border-[#2d3748]">
                                <div className="text-xs font-semibold text-[#6b7280] dark:text-[#9ca3af] mb-2 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[14px]">library_books</span>
                                    Sources
                                </div>
                                <div className="space-y-1">
                                    {message.citations.map((citation, idx) => (
                                        <div
                                            key={idx}
                                            className="text-xs text-[#6b7280] dark:text-[#9ca3af] flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer group/citation"
                                        >
                                            <span className="material-symbols-outlined text-[14px] group-hover/citation:scale-110 transition-transform">article</span>
                                            <span className="flex-1">{citation.source}</span>
                                            <span className="text-[10px] opacity-60">Page {citation.page}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Inline Approval UI */}
                        {message.approvalRequest && (
                            <div className="mt-4 pt-4 border-t border-[#e7ebf3] dark:border-[#2d3748]">
                                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mb-3 border border-blue-100 dark:border-blue-800">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-[18px]">mail</span>
                                        <span className="text-xs font-bold text-blue-800 dark:text-blue-200">Email Draft</span>
                                    </div>
                                    <div className="text-sm font-medium text-slate-900 dark:text-white mb-1">
                                        {message.approvalRequest.draft.subject}
                                    </div>
                                    <div className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                                        {message.approvalRequest.draft.body}
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    {onApprove && (
                                        <button
                                            onClick={async () => {
                                                const btn = document.activeElement as HTMLButtonElement;
                                                btn.disabled = true;
                                                btn.innerHTML = '<span class="size-3 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>Sending...';
                                                await onApprove(message.approvalRequest!.request_id);
                                                // No need to reset as message will update/disappear
                                            }}
                                            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-semibold py-2 rounded-lg shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-1.5 disabled:opacity-75 disabled:cursor-not-allowed"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">check_circle</span>
                                            Approve & Send
                                        </button>
                                    )}
                                    {onDecline && (
                                        <button
                                            onClick={() => onDecline(message.approvalRequest!.request_id)}
                                            className="px-4 bg-white dark:bg-[#1a202c] border border-gray-200 dark:border-gray-700 text-red-600 dark:text-red-400 text-xs font-semibold py-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors flex items-center gap-1.5"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">cancel</span>
                                            Decline
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Reactions */}
                        {message.reactions && message.reactions.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-3 pt-2 border-t border-[#e7ebf3] dark:border-[#2d3748]">
                                {message.reactions.map((reaction, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleReact(reaction.emoji)}
                                        className="flex items-center gap-1 px-2 py-1 bg-slate-50 dark:bg-slate-800 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-xs"
                                        title={reaction.users.join(', ')}
                                    >
                                        <span>{reaction.emoji}</span>
                                        <span className="text-[10px] font-semibold text-slate-600 dark:text-slate-400">{reaction.count}</span>
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Timestamp */}
                        <div className={`text-[10px] mt-2.5 flex items-center gap-2 ${message.role === 'user' ? 'text-white/70 justify-end' : 'text-[#9ca3af]'}`}>
                            <span>{message.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                            {message.role === 'agent' && (
                                <>
                                    <span>•</span>
                                    <span className="flex items-center gap-1">
                                        <span className="material-symbols-outlined text-[10px]">verified</span>
                                        AI Generated
                                    </span>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Suggestions */}
                    {message.suggestions && message.suggestions.length > 0 && (
                        <div className="flex flex-col gap-2 mt-3 animate-in fade-in slide-in-from-top-1 duration-500 delay-300">
                            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 pl-1">
                                <span className="material-symbols-outlined text-[14px]">lightbulb</span>
                                <span className="font-medium">Suggested follow-ups</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {message.suggestions.map((suggestion, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => onSuggestionClick?.(suggestion)}
                                        className="text-left text-xs bg-white dark:bg-[#1a202c] border border-blue-200 dark:border-blue-900/50 text-slate-700 dark:text-slate-300 px-3 py-2 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:border-blue-300 dark:hover:border-blue-700 hover:text-blue-700 dark:hover:text-blue-200 transition-all shadow-sm hover:shadow-md active:scale-95"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Action buttons */}
                    {showActions && (
                        <div className={`absolute ${message.role === 'user' ? 'left-0 -translate-x-full' : 'right-0 translate-x-full'} top-2 flex items-center gap-1 px-2 animate-in fade-in slide-in-from-right-2 duration-200`}>
                            {/* Copy button */}
                            <button
                                onClick={handleCopy}
                                className="p-1.5 bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-lg shadow-md hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                title={copied ? 'Copied!' : 'Copy message'}
                            >
                                <span className="material-symbols-outlined text-[16px] text-slate-600 dark:text-slate-400">
                                    {copied ? 'check' : 'content_copy'}
                                </span>
                            </button>

                            {/* React button */}
                            <div className="relative">
                                <button
                                    onClick={() => setShowReactions(!showReactions)}
                                    className="p-1.5 bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-lg shadow-md hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                    title="Add reaction"
                                >
                                    <span className="material-symbols-outlined text-[16px] text-slate-600 dark:text-slate-400">add_reaction</span>
                                </button>

                                {/* Reaction picker */}
                                {showReactions && (
                                    <div className="absolute top-full mt-1 right-0 bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-lg shadow-xl p-2 flex gap-1 animate-in fade-in slide-in-from-top-2 duration-200 z-10">
                                        {commonReactions.map((emoji) => (
                                            <button
                                                key={emoji}
                                                onClick={() => handleReact(emoji)}
                                                className="p-2 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors text-lg hover:scale-125 transition-transform"
                                            >
                                                {emoji}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Reply button */}
                            {onReply && (
                                <button
                                    onClick={() => onReply(message.id)}
                                    className="p-1.5 bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-lg shadow-md hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                    title="Reply"
                                >
                                    <span className="material-symbols-outlined text-[16px] text-slate-600 dark:text-slate-400">reply</span>
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {message.role === 'user' && (
                <div className="size-9 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center shrink-0 shadow-md">
                    <span className="material-symbols-outlined text-white text-[18px]">person</span>
                </div>
            )}
        </div>
    );
}
