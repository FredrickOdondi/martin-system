import { useState, useRef, useEffect } from 'react';
import { ChatMessage, ChatMessageType, EnhancedChatRequest, ActionType } from '../../types/agent';
import { useStreamingChat, StreamEvent } from '../../hooks/useStreamingChat';

export default function CopilotChat() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [conversationId, setConversationId] = useState<string | undefined>(undefined);

    const { streamingState, sendStreamingMessage, cancelStream } = useStreamingChat();
    const { isStreaming, currentStatus, currentTool } = streamingState;

    // Initial Welcome Message
    useEffect(() => {
        if (messages.length === 0) {
            setMessages([
                {
                    message_id: 'welcome',
                    conversation_id: 'init',
                    message_type: ChatMessageType.AGENT_TEXT,
                    content: "Hello Dr. Sow. I can help you analyze documents, draft agendas, and coordinate with other TWGs. How can I assist you today?",
                    sender: 'agent',
                    timestamp: new Date().toISOString()
                }
            ]);
        }
    }, [messages.length]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingState]);

    const handleSendMessage = async () => {
        if (!input.trim() || isStreaming) return;

        const content = input.trim();
        setInput('');

        const userMsg: ChatMessage = {
            message_id: Date.now().toString(),
            conversation_id: conversationId || '',
            message_type: ChatMessageType.USER_TEXT,
            content: content,
            sender: 'user',
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMsg]);

        const request: EnhancedChatRequest = {
            message: content,
            conversation_id: conversationId
        };

        await sendStreamingMessage(
            request,
            (event: StreamEvent) => {
                if (event.type === 'start' && event.conversation_id) {
                    setConversationId(event.conversation_id);
                }
                // We could handle intermediate events here if needed, 
                // but streamingState handles status/tool updates automatically
            },
            (finalMsg: any) => {
                setMessages(prev => [...prev, finalMsg]);
            },
            (err: string) => {
                setMessages(prev => [...prev, {
                    message_id: Date.now().toString(),
                    conversation_id: conversationId || '',
                    message_type: ChatMessageType.SYSTEM,
                    content: `Error: ${err}`,
                    sender: 'system',
                    timestamp: new Date().toISOString()
                }]);
            }
        );
    };

    return (
        <div className="flex flex-col h-full bg-white dark:bg-dark-card">
            {/* Header */}
            <div className="p-4 border-b border-slate-100 dark:border-dark-border flex items-center justify-between transition-colors">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-900/20">
                        <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                    </div>
                    <div>
                        <h3 className="font-bold text-sm text-slate-900 dark:text-white">ECOWAS AI Copilot</h3>
                        <p className="text-[10px] text-green-500 font-bold uppercase flex items-center gap-1 transition-colors">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            Online • Energy Context
                        </p>
                    </div>
                </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={msg.message_id || idx} className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                        {msg.sender !== 'user' && (
                            <div className="w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 transition-colors">
                                {msg.sender === 'system' ? (
                                    <span className="material-symbols-outlined text-[14px] text-red-500">warning</span>
                                ) : (
                                    <span className="material-symbols-outlined text-[14px] text-blue-600">smart_toy</span>
                                )}
                            </div>
                        )}
                        <div className={`
                            p-3 rounded-2xl max-w-[85%] text-xs leading-relaxed transition-colors shadow-sm
                            ${msg.sender === 'user'
                                ? 'bg-blue-600 text-white rounded-tr-none'
                                : msg.sender === 'system'
                                    ? 'bg-red-50 text-red-600 border border-red-100'
                                    : 'bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 rounded-tl-none border border-slate-100 dark:border-slate-700'
                            }
                        `}>
                            <p>{msg.content}</p>

                            {/* Render Tool Execution Metadata */}
                            {msg.metadata?.parsed?.type === 'command_result' && (
                                <div className="mt-2 pt-2 border-t border-black/10 dark:border-white/10 text-[10px] opacity-70 font-mono flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[10px]">terminal</span>
                                    Executed: {msg.metadata.parsed.command}
                                </div>
                            )}

                            {/* Render Actions (Buttons) */}
                            {msg.actions && msg.actions.length > 0 && (
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {msg.actions.map(action => (
                                        <button
                                            key={action.action_id}
                                            className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wide transition-colors ${action.style === 'primary'
                                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                                : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
                                                }`}
                                            onClick={() => {
                                                if (action.action_type === ActionType.BUTTON) {
                                                    setInput(action.value || action.label);
                                                    // Optional: auto-submit?
                                                }
                                            }}
                                        >
                                            {action.icon && <span className="material-symbols-outlined text-[12px] mr-1 align-bottom">{action.icon}</span>}
                                            {action.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isStreaming && (
                    <div className="flex gap-3">
                        <div className="w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 transition-colors">
                            <span className="material-symbols-outlined text-[14px] text-blue-600 animate-spin">sync</span>
                        </div>
                        <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl rounded-tl-none transition-colors border border-slate-100 dark:border-slate-700">
                            <div className="flex flex-col gap-1">
                                <p className="text-xs text-slate-500 dark:text-slate-400 font-bold animate-pulse">
                                    {currentStatus || 'Thinking...'}
                                </p>
                                {currentTool && (
                                    <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
                                        <span className="material-symbols-outlined text-[10px]">build</span>
                                        Using: {currentTool}
                                    </div>
                                )}
                            </div>
                        </div>
                        <button
                            onClick={cancelStream}
                            className="w-6 h-6 rounded-full bg-slate-100 hover:bg-red-100 text-slate-400 hover:text-red-500 flex items-center justify-center transition-colors"
                            title="Stop generating"
                        >
                            <span className="material-symbols-outlined text-[14px]">stop</span>
                        </button>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-3 border-t border-slate-100 dark:border-dark-border bg-slate-50/50 dark:bg-slate-800/20">
                <div className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="Ask Copilot to analyze, draft, or schedule..."
                        className="w-full bg-white dark:bg-dark-elem border border-slate-200 dark:border-slate-600 rounded-xl py-3 pl-4 pr-12 text-xs font-medium text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 hover:border-blue-400 transition-all shadow-sm"
                        disabled={isStreaming}
                        autoFocus
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={!input.trim() || isStreaming}
                        className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors shadow-md shadow-blue-900/20"
                    >
                        <span className="material-symbols-outlined text-[16px] block">send</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
