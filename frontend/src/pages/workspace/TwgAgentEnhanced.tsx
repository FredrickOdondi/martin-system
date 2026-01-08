import { useState, useRef, useEffect } from 'react';
import { agentService, Citation } from '../../services/agentService';
import { CommandAutocomplete } from '../../components/agent/CommandAutocomplete';
import { MentionAutocomplete } from '../../components/agent/MentionAutocomplete';
import EmailApprovalModal, { EmailApprovalRequest, EmailDraft } from '../../components/agent/EmailApprovalModal';
import SettingsModal from '../../components/agent/SettingsModal';
import EnhancedMessageBubble from '../../components/agent/EnhancedMessageBubble';
import TypingIndicator from '../../components/agent/TypingIndicator';
import WorkspaceContextPanel from '../../components/workspace/WorkspaceContextPanel';
import { CommandAutocompleteResult } from '../../types/agent';
import axios from 'axios';

interface Message {
    id: string;
    role: 'user' | 'agent';
    content: string;
    timestamp: Date;
    citations?: Citation[];
    reactions?: MessageReaction[];
    agentName?: string;
    agentIcon?: string;
}

interface MessageReaction {
    emoji: string;
    count: number;
    users: string[];
}

interface AgentMentionSuggestion {
    mention: string;
    agent_id: string;
    name: string;
    icon: string;
    description: string;
    match_score?: number;
}

export default function TwgAgentEnhanced() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | undefined>();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Autocomplete state
    const [commandSuggestions, setCommandSuggestions] = useState<CommandAutocompleteResult[]>([]);
    const [mentionSuggestions, setMentionSuggestions] = useState<AgentMentionSuggestion[]>([]);
    const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);
    const [autocompleteType, setAutocompleteType] = useState<'command' | 'mention' | null>(null);

    // Email approval state
    const [pendingEmailApproval, setPendingEmailApproval] = useState<EmailApprovalRequest | null>(null);
    const [showApprovalModal, setShowApprovalModal] = useState(false);

    // Sidebar state
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    // Settings modal state
    const [showSettingsModal, setShowSettingsModal] = useState(false);

    // Context panel state
    const [showContextPanel, setShowContextPanel] = useState(true);

    // Typing state
    const [typingMessage, setTypingMessage] = useState<string | null>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading, typingMessage]);

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputMessage,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        const messageToSend = inputMessage;
        setInputMessage('');
        setIsLoading(true);

        // Show typing indicator with context
        setTypingMessage('Processing your request...');

        // Create new AbortController for this request
        abortControllerRef.current = new AbortController();

        try {
            const response = await agentService.chat({
                message: messageToSend,
                conversation_id: conversationId,
            });

            setConversationId(response.conversation_id);
            setTypingMessage(null);

            // Check if response contains an email approval request
            if (response.response.includes('Approval Required') || response.response.includes('approval_request_id')) {
                try {
                    const approvalMatch = response.response.match(/(?:approval_request_id|Approval Request ID)['":\s`*]+([a-f0-9-]{36})/i);
                    if (approvalMatch) {
                        const requestId = approvalMatch[1];
                        const approvalData = await agentService.getEmailApproval(requestId);
                        setPendingEmailApproval(approvalData);
                        setShowApprovalModal(true);
                    }
                } catch (err) {
                    console.error('Error fetching approval request:', err);
                }
            }

            const agentMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'agent',
                content: response.response,
                timestamp: new Date(),
                citations: response.citations,
                agentName: 'Secretariat Assistant',
            };

            setMessages(prev => [...prev, agentMessage]);
        } catch (error: any) {
            setTypingMessage(null);
            if (error?.name === 'AbortError' || error?.message?.includes('abort')) {
                console.log('Request aborted by user');
            } else {
                console.error('Error sending message:', error);
                const errorMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'agent',
                    content: 'Sorry, I encountered an error processing your request. Please try again.',
                    timestamp: new Date(),
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } finally {
            setIsLoading(false);
            abortControllerRef.current = null;
        }
    };

    // Detect slash commands and @mentions in input
    const handleInputChange = async (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const value = e.target.value;
        setInputMessage(value);

        const cursorPosition = e.target.selectionStart;
        const textBeforeCursor = value.substring(0, cursorPosition);

        // Check for command trigger (/)
        const commandMatch = textBeforeCursor.match(/\/(\w*)$/);
        if (commandMatch) {
            const query = '/' + commandMatch[1];
            try {
                const response = await axios.get(`/api/agents/commands/autocomplete`, {
                    params: { query }
                });
                setCommandSuggestions(response.data.suggestions);
                setAutocompleteType('command');
                setSelectedSuggestionIndex(0);
                return;
            } catch (error) {
                console.error('Error fetching command suggestions:', error);
            }
        }

        // Check for mention trigger (@)
        const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
        if (mentionMatch) {
            const query = '@' + mentionMatch[1];
            try {
                const response = await axios.get(`/api/agents/mentions/autocomplete`, {
                    params: { query }
                });
                setMentionSuggestions(response.data.suggestions);
                setAutocompleteType('mention');
                setSelectedSuggestionIndex(0);
                return;
            } catch (error) {
                console.error('Error fetching mention suggestions:', error);
            }
        }

        // Clear autocomplete if no trigger detected
        setAutocompleteType(null);
        setCommandSuggestions([]);
        setMentionSuggestions([]);
    };

    const handleCommandSelect = (suggestion: CommandAutocompleteResult) => {
        const cursorPosition = inputRef.current?.selectionStart || 0;
        const textBeforeCursor = inputMessage.substring(0, cursorPosition);
        const textAfterCursor = inputMessage.substring(cursorPosition);

        const commandMatch = textBeforeCursor.match(/\/(\w*)$/);
        if (commandMatch) {
            const beforeCommand = textBeforeCursor.substring(0, textBeforeCursor.length - commandMatch[0].length);
            const newValue = beforeCommand + suggestion.command + ' ' + textAfterCursor;
            setInputMessage(newValue);
            setAutocompleteType(null);
            setCommandSuggestions([]);

            setTimeout(() => {
                if (inputRef.current) {
                    const newCursorPos = beforeCommand.length + suggestion.command.length + 1;
                    inputRef.current.focus();
                    inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
                }
            }, 0);
        }
    };

    const handleMentionSelect = (suggestion: AgentMentionSuggestion) => {
        const cursorPosition = inputRef.current?.selectionStart || 0;
        const textBeforeCursor = inputMessage.substring(0, cursorPosition);
        const textAfterCursor = inputMessage.substring(cursorPosition);

        const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
        if (mentionMatch) {
            const beforeMention = textBeforeCursor.substring(0, textBeforeCursor.length - mentionMatch[0].length);
            const newValue = beforeMention + suggestion.mention + ' ' + textAfterCursor;
            setInputMessage(newValue);
            setAutocompleteType(null);
            setMentionSuggestions([]);

            setTimeout(() => {
                if (inputRef.current) {
                    const newCursorPos = beforeMention.length + suggestion.mention.length + 1;
                    inputRef.current.focus();
                    inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
                }
            }, 0);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (autocompleteType) {
            const suggestions = autocompleteType === 'command' ? commandSuggestions : mentionSuggestions;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedSuggestionIndex((prev) => (prev + 1) % suggestions.length);
                return;
            }

            if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedSuggestionIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
                return;
            }

            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (autocompleteType === 'command' && commandSuggestions[selectedSuggestionIndex]) {
                    handleCommandSelect(commandSuggestions[selectedSuggestionIndex]);
                } else if (autocompleteType === 'mention' && mentionSuggestions[selectedSuggestionIndex]) {
                    handleMentionSelect(mentionSuggestions[selectedSuggestionIndex]);
                }
                return;
            }

            if (e.key === 'Escape') {
                e.preventDefault();
                setAutocompleteType(null);
                setCommandSuggestions([]);
                setMentionSuggestions([]);
                return;
            }
        }

        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleClearConversation = () => {
        if (messages.length === 0 && !isLoading) return;

        if (window.confirm('Are you sure you want to clear this conversation? This action cannot be undone.')) {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
                abortControllerRef.current = null;
            }

            setMessages([]);
            setConversationId(undefined);
            setIsLoading(false);
            setTypingMessage(null);
        }
    };

    const handleReact = (messageId: string, emoji: string) => {
        setMessages(prev => prev.map(msg => {
            if (msg.id === messageId) {
                const reactions = msg.reactions || [];
                const existingReaction = reactions.find(r => r.emoji === emoji);

                if (existingReaction) {
                    return {
                        ...msg,
                        reactions: reactions.map(r =>
                            r.emoji === emoji
                                ? { ...r, count: r.count + 1, users: [...r.users, 'You'] }
                                : r
                        )
                    };
                } else {
                    return {
                        ...msg,
                        reactions: [...reactions, { emoji, count: 1, users: ['You'] }]
                    };
                }
            }
            return msg;
        }));
    };

    const handleInsertContext = (contextType: string, data: any) => {
        let contextText = '';

        switch (contextType) {
            case 'meeting':
                contextText = `Please summarize the meeting "${data.title}" scheduled for ${data.date}`;
                break;
            case 'action':
                contextText = `What is the status of the action item: "${data.task}" assigned to ${data.assignee}?`;
                break;
            case 'document':
                contextText = `Can you provide information about the document "${data.name}"?`;
                break;
            case 'template':
                if (data.type === 'summary') {
                    contextText = 'Generate a summary of all recent TWG activities';
                } else if (data.type === 'stats') {
                    contextText = 'Show me the statistics for this TWG workspace';
                }
                break;
            default:
                contextText = `Context: ${JSON.stringify(data)}`;
        }

        setInputMessage(contextText);
        inputRef.current?.focus();
    };

    const handleApproveEmail = async (requestId: string, modifications?: EmailDraft) => {
        try {
            const approvalData = {
                request_id: requestId,
                approved: true,
                modifications: modifications || null
            };

            const result = await agentService.approveEmail(requestId, approvalData);

            setShowApprovalModal(false);
            setPendingEmailApproval(null);

            const successMessage: Message = {
                id: Date.now().toString(),
                role: 'agent',
                content: result.email_sent
                    ? `✅ Email sent successfully! Message ID: ${result.message_id}`
                    : `⚠️ ${result.message}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, successMessage]);
        } catch (error) {
            console.error('Error approving email:', error);
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'agent',
                content: `❌ Failed to send email: ${error}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        }
    };

    const handleDeclineEmail = async (requestId: string, reason?: string) => {
        try {
            await agentService.declineEmail(requestId, reason);

            setShowApprovalModal(false);
            setPendingEmailApproval(null);

            const declineMessage: Message = {
                id: Date.now().toString(),
                role: 'agent',
                content: `🚫 Email sending cancelled: ${reason || 'Declined by user'}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, declineMessage]);
        } catch (error) {
            console.error('Error declining email:', error);
        }
    };

    return (
        <div className="font-display bg-background-light dark:bg-background-dark text-[#0d121b] dark:text-white h-screen flex flex-col overflow-hidden">
            {/* Top Navbar */}
            <header className="sticky top-0 z-50 w-full bg-white dark:bg-[#1a202c] border-b border-[#e7ebf3] dark:border-[#2d3748] shrink-0">
                <div className="px-6 lg:px-10 py-3 flex items-center justify-between gap-6">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-3">
                            <div className="size-8 rounded-full bg-[#1152d4]/10 flex items-center justify-center text-[#1152d4]">
                                <span className="material-symbols-outlined">shield_person</span>
                            </div>
                            <h2 className="text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">ECOWAS Summit TWG Support</h2>
                        </div>
                        <div className="hidden md:flex items-center bg-[#f0f2f5] dark:bg-[#2d3748] rounded-lg h-10 w-64 px-3 gap-2">
                            <span className="material-symbols-outlined text-[#4c669a] dark:text-[#a0aec0]">search</span>
                            <input
                                className="bg-transparent border-none outline-none text-sm w-full placeholder:text-[#4c669a] dark:placeholder:text-[#a0aec0] text-[#0d121b] dark:text-white focus:ring-0 p-0"
                                placeholder="Search Workspace..."
                                type="text"
                            />
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <nav className="hidden lg:flex items-center gap-6">
                            <a className="text-[#4c669a] dark:text-[#a0aec0] hover:text-[#1152d4] dark:hover:text-white text-sm font-medium transition-colors" href="/dashboard">Dashboard</a>
                            <a className="text-[#1152d4] dark:text-white text-sm font-medium transition-colors" href="/twgs">TWGs</a>
                            <a className="text-[#4c669a] dark:text-[#a0aec0] hover:text-[#1152d4] dark:hover:text-white text-sm font-medium transition-colors" href="#">Reports</a>
                            <a className="text-[#4c669a] dark:text-[#a0aec0] hover:text-[#1152d4] dark:hover:text-white text-sm font-medium transition-colors" href="#">Settings</a>
                        </nav>
                        <div className="flex items-center gap-4 border-l border-[#e7ebf3] dark:border-[#2d3748] pl-6">
                            <button className="relative text-[#4c669a] dark:text-[#a0aec0] hover:text-[#1152d4] dark:hover:text-white transition-colors">
                                <span className="material-symbols-outlined">notifications</span>
                            </button>
                            <div className="h-10 w-10 rounded-full bg-cover bg-center border border-[#e7ebf3] dark:border-[#2d3748] bg-gray-300"></div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 flex overflow-hidden">
                {/* Sidebar - Agent List */}
                <aside className={`${isSidebarCollapsed ? 'w-0' : 'w-80'} bg-white dark:bg-[#1a202c] border-r border-[#e7ebf3] dark:border-[#2d3748] flex flex-col transition-all duration-300 overflow-hidden hidden lg:flex`}>
                    <div className="p-6 border-b border-[#e7ebf3] dark:border-[#2d3748]">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-xs font-bold text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider">Active Workspace</div>
                            <button
                                onClick={() => setIsSidebarCollapsed(true)}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-[#2d3748] rounded transition-colors"
                                title="Collapse sidebar"
                            >
                                <span className="material-symbols-outlined text-[18px] text-[#6b7280]">chevron_left</span>
                            </button>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="size-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-[#1152d4] flex items-center justify-center">
                                <span className="material-symbols-outlined">bolt</span>
                            </div>
                            <div>
                                <h3 className="font-bold text-[#0d121b] dark:text-white leading-tight">Energy TWG</h3>
                                <p className="text-xs text-[#4c669a] dark:text-[#a0aec0]">Member States: 15</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-6">
                        <div>
                            <h4 className="px-2 text-xs font-bold text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider mb-3">AI Agents</h4>
                            <div className="space-y-1">
                                <button className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#1152d4]/10 text-[#1152d4] dark:text-blue-400 rounded-lg transition-colors">
                                    <div className="relative">
                                        <span className="material-symbols-outlined">smart_toy</span>
                                        <span className="absolute -bottom-0.5 -right-0.5 size-2.5 border-2 border-white dark:border-[#1a202c] bg-green-500 rounded-full"></span>
                                    </div>
                                    <div className="text-left flex-1">
                                        <div className="font-bold text-sm">Secretariat Assistant</div>
                                        <div className="text-[11px] opacity-80">Main Coordinator</div>
                                    </div>
                                </button>

                                {/* TWG Agents - shortened for brevity */}
                                <button className="w-full flex items-center gap-3 px-3 py-2.5 text-[#4c669a] dark:text-[#a0aec0] hover:bg-gray-50 dark:hover:bg-[#2d3748] rounded-lg transition-colors">
                                    <div className="relative size-8 rounded-full bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center flex-shrink-0">
                                        <span className="material-symbols-outlined text-white text-[16px]">bolt</span>
                                        <span className="absolute -bottom-0.5 -right-0.5 size-2.5 border-2 border-white dark:border-[#1a202c] bg-green-500 rounded-full"></span>
                                    </div>
                                    <div className="text-left flex-1">
                                        <div className="font-medium text-sm text-[#0d121b] dark:text-white">Energy Agent</div>
                                        <div className="text-[11px] opacity-70">@EnergyAgent</div>
                                    </div>
                                </button>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Chat Area */}
                <div className="flex-1 flex flex-col bg-[#f6f6f8] dark:bg-[#0d121b]">
                    {/* Agent Header */}
                    <div className="bg-white dark:bg-[#1a202c] border-b border-[#e7ebf3] dark:border-[#2d3748] px-6 py-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {isSidebarCollapsed && (
                                <button
                                    onClick={() => setIsSidebarCollapsed(false)}
                                    className="p-2 hover:bg-gray-100 dark:hover:bg-[#2d3748] rounded-lg transition-colors"
                                    title="Expand sidebar"
                                >
                                    <span className="material-symbols-outlined text-[#6b7280]">menu</span>
                                </button>
                            )}
                            <div className="relative">
                                <div className="size-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white">
                                    <span className="material-symbols-outlined">smart_toy</span>
                                </div>
                                <span className="absolute bottom-0 right-0 size-3 border-2 border-white dark:border-[#1a202c] bg-green-500 rounded-full"></span>
                            </div>
                            <div>
                                <h3 className="font-bold text-[#0d121b] dark:text-white">Secretariat Assistant</h3>
                                <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                                    <span className="size-1.5 bg-green-500 rounded-full"></span>
                                    Online
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setShowContextPanel(!showContextPanel)}
                                className={`p-2 rounded-lg transition-colors ${
                                    showContextPanel
                                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                                        : 'text-[#4c669a] hover:bg-gray-100 dark:hover:bg-[#2d3748]'
                                }`}
                                title="Toggle workspace context"
                            >
                                <span className="material-symbols-outlined">view_sidebar</span>
                            </button>
                            {isLoading && (
                                <button
                                    onClick={() => {
                                        if (abortControllerRef.current) {
                                            abortControllerRef.current.abort();
                                            abortControllerRef.current = null;
                                        }
                                        setIsLoading(false);
                                        setTypingMessage(null);
                                    }}
                                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                    title="Stop generation"
                                >
                                    <span className="material-symbols-outlined">stop_circle</span>
                                </button>
                            )}
                            <button
                                onClick={() => setShowSettingsModal(true)}
                                className="p-2 text-[#4c669a] hover:bg-gray-100 dark:hover:bg-[#2d3748] rounded-lg transition-colors"
                                title="Settings"
                            >
                                <span className="material-symbols-outlined">settings</span>
                            </button>
                            <button
                                onClick={handleClearConversation}
                                className="p-2 text-[#4c669a] hover:bg-gray-100 dark:hover:bg-[#2d3748] rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Clear conversation"
                                disabled={messages.length === 0 && !isLoading}
                            >
                                <span className="material-symbols-outlined">delete</span>
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-gradient-to-b from-gray-50/50 to-transparent dark:from-[#0d121b]/30 dark:to-transparent">
                        {messages.length === 0 ? (
                            <div className="h-full flex items-center justify-center px-4">
                                <div className="max-w-4xl w-full text-center">
                                    <div className="size-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center backdrop-blur-sm">
                                        <span className="material-symbols-outlined text-blue-600 dark:text-blue-400" style={{ fontSize: '48px' }}>chat_bubble</span>
                                    </div>
                                    <h3 className="text-2xl font-semibold text-[#0d121b] dark:text-white mb-3">Welcome to ECOWAS Summit Assistant</h3>
                                    <p className="text-base text-[#6b7280] dark:text-[#9ca3af] max-w-xl mx-auto leading-relaxed mb-6">
                                        I'm here to help with TWG coordination, document drafting, and summit preparation. What can I assist you with today?
                                    </p>
                                    {showContextPanel && (
                                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                                            <span className="material-symbols-outlined text-[18px]">lightbulb</span>
                                            <span>Tip: Use the context panel on the right to reference meetings, actions, and documents</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            messages.map((message) => (
                                <EnhancedMessageBubble
                                    key={message.id}
                                    message={message}
                                    onReact={handleReact}
                                />
                            ))
                        )}
                        {(isLoading || typingMessage) && (
                            <TypingIndicator
                                agentName="Secretariat Assistant"
                                message={typingMessage || undefined}
                            />
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="bg-white dark:bg-[#1a202c] border-t border-[#e7ebf3] dark:border-[#2d3748] p-4">
                        <div className="flex gap-2 mb-3 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
                            <button className="shrink-0 text-xs font-medium px-4 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 text-blue-700 dark:text-blue-300 transition-all flex items-center gap-1.5 border border-blue-200 dark:border-blue-800 hover:shadow-sm">
                                <span className="material-symbols-outlined text-[16px]">description</span>
                                Draft Minutes
                            </button>
                            <button className="shrink-0 text-xs font-medium px-4 py-2 rounded-lg bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 text-purple-700 dark:text-purple-300 transition-all flex items-center gap-1.5 border border-purple-200 dark:border-purple-800 hover:shadow-sm">
                                <span className="material-symbols-outlined text-[16px]">summarize</span>
                                Summarize Last Session
                            </button>
                            <button className="shrink-0 text-xs font-medium px-4 py-2 rounded-lg bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 text-green-700 dark:text-green-300 transition-all flex items-center gap-1.5 border border-green-200 dark:border-green-800 hover:shadow-sm">
                                <span className="material-symbols-outlined text-[16px]">calendar_month</span>
                                Check Availability
                            </button>
                        </div>

                        <div className="relative bg-white dark:bg-[#0d121b] border-2 border-[#e7ebf3] dark:border-[#2d3748] rounded-2xl shadow-lg focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500 dark:focus-within:border-blue-400 transition-all">
                            {autocompleteType === 'command' && commandSuggestions.length > 0 && (
                                <CommandAutocomplete
                                    suggestions={commandSuggestions}
                                    selectedIndex={selectedSuggestionIndex}
                                    onSelect={handleCommandSelect}
                                    onHover={setSelectedSuggestionIndex}
                                />
                            )}

                            {autocompleteType === 'mention' && mentionSuggestions.length > 0 && (
                                <MentionAutocomplete
                                    suggestions={mentionSuggestions}
                                    selectedIndex={selectedSuggestionIndex}
                                    onSelect={handleMentionSelect}
                                    onHover={setSelectedSuggestionIndex}
                                />
                            )}

                            <textarea
                                ref={inputRef}
                                value={inputMessage}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyPress}
                                disabled={isLoading}
                                className="w-full bg-transparent border-none focus:ring-0 text-sm p-4 pr-36 min-h-[60px] max-h-32 resize-none text-[#0d121b] dark:text-white placeholder:text-[#9ca3af] disabled:opacity-50"
                                placeholder="Ask me anything... Use / for commands or @ for agents"
                            />
                            <div className="absolute bottom-3 right-3 flex items-center gap-1.5">
                                <button className="p-2 text-[#6b7280] dark:text-[#9ca3af] hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all" title="Attach file">
                                    <span className="material-symbols-outlined text-[20px]">attach_file</span>
                                </button>
                                <button className="p-2 text-[#6b7280] dark:text-[#9ca3af] hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all" title="Voice input">
                                    <span className="material-symbols-outlined text-[20px]">mic</span>
                                </button>
                                <div className="w-px h-6 bg-[#e7ebf3] dark:bg-[#2d3748] mx-1"></div>
                                <button
                                    onClick={handleSendMessage}
                                    disabled={!inputMessage.trim() || isLoading}
                                    className="p-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md"
                                    title="Send message"
                                >
                                    <span className="material-symbols-outlined text-[20px]">send</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Workspace Context Panel */}
                {showContextPanel && (
                    <WorkspaceContextPanel
                        twgName="Energy TWG"
                        onInsertContext={handleInsertContext}
                    />
                )}
            </main>

            {/* Modals */}
            {showApprovalModal && pendingEmailApproval && (
                <EmailApprovalModal
                    approvalRequest={pendingEmailApproval}
                    onApprove={handleApproveEmail}
                    onDecline={handleDeclineEmail}
                    onClose={() => {
                        setShowApprovalModal(false);
                        setPendingEmailApproval(null);
                    }}
                />
            )}

            {showSettingsModal && (
                <SettingsModal
                    onClose={() => setShowSettingsModal(false)}
                />
            )}
        </div>
    );
}
