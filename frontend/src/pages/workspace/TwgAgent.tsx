import { useState, useRef, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { agentService, Citation } from '../../services/agentService';
import { twgService } from '../../services/twgService';
import { CommandAutocomplete } from '../../components/agent/CommandAutocomplete';
import { MentionAutocomplete } from '../../components/agent/MentionAutocomplete';
import EmailApprovalModal, { EmailApprovalRequest, EmailDraft } from '../../components/agent/EmailApprovalModal';
import SettingsModal from '../../components/agent/SettingsModal';
import { CommandAutocompleteResult } from '../../types/agent';



interface Message {
    id: string;
    role: 'user' | 'agent';
    content: string;
    timestamp: Date;
    citations?: Citation[];
}

// Function to parse and format markdown-like text
const formatMarkdownText = (text: string): JSX.Element => {
    const lines = text.split('\n');
    const elements: JSX.Element[] = [];

    lines.forEach((line, index) => {
        // Remove markdown bold syntax
        let formattedLine = line.replace(/\*\*(.*?)\*\*/g, '$1');

        // Handle numbered lists
        if (/^\d+\.\s/.test(formattedLine)) {
            const content = formattedLine.replace(/^\d+\.\s/, '');
            elements.push(
                <div key={index} className="mb-2">
                    <span className="font-semibold">{content}</span>
                </div>
            );
        }
        // Handle bullet points with - or *
        else if (/^\s*[-*]\s/.test(formattedLine)) {
            const indent = formattedLine.search(/[-*]/);
            const content = formattedLine.replace(/^\s*[-*]\s/, '');
            elements.push(
                <div key={index} className="mb-1" style={{ paddingLeft: `${indent * 8}px` }}>
                    • {content}
                </div>
            );
        }
        // Empty lines
        else if (formattedLine.trim() === '') {
            elements.push(<div key={index} className="h-2"></div>);
        }
        // Regular text
        else {
            elements.push(
                <div key={index} className="mb-1">
                    {formattedLine}
                </div>
            );
        }
    });

    return <>{elements}</>;
}

interface AgentMentionSuggestion {
    mention: string;
    agent_id: string;
    name: string;
    icon: string;
    description: string;
    match_score?: number;
}

export default function TwgAgent() {
    // User context for dynamic agent routing
    const user = useSelector((state: RootState) => state.auth.user);
    const twgId = user?.role !== 'admin' ? user?.twg_ids?.[0] : undefined;

    // Agent name state (fetched from TWG)
    const [agentName, setAgentName] = useState<string>('Your Assistant');

    // Fetch TWG details to get the proper agent name
    useEffect(() => {
        const fetchTwgDetails = async () => {
            if (!twgId) {
                setAgentName('Secretariat Assistant');
                return;
            }
            try {
                const twg = await twgService.getTWG(twgId);
                // Extract pillar name from TWG name (e.g., "Energy TWG" -> "Energy Agent")
                const pillarName = twg.name.replace(' TWG', '').replace('TWG', '').trim();
                setAgentName(`${pillarName} Agent`);
            } catch (error) {
                console.error('Failed to fetch TWG details:', error);
                setAgentName('Your TWG Agent');
            }
        };
        fetchTwgDetails();
    }, [twgId]);

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

    // Settings modal state
    const [showSettingsModal, setShowSettingsModal] = useState(false);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

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

        // Create new AbortController for this request
        abortControllerRef.current = new AbortController();

        try {
            const response = await agentService.chat({
                message: messageToSend,
                conversation_id: conversationId,
                twg_id: twgId,
            });

            setConversationId(response.conversation_id);

            // Check if response contains an email approval request
            if (response.response.includes('Approval Required') || response.response.includes('approval_request_id')) {
                try {
                    // Try to extract approval request ID from response (handles markdown backticks)
                    const approvalMatch = response.response.match(/(?:approval_request_id|Approval Request ID)['":\s`*]+([a-f0-9-]{36})/i);
                    if (approvalMatch) {
                        const requestId = approvalMatch[1];
                        console.log('Found approval request ID:', requestId);

                        // Fetch the full approval request
                        const approvalData = await agentService.getEmailApproval(requestId);
                        console.log('Fetched approval data:', approvalData);

                        setPendingEmailApproval(approvalData);
                        setShowApprovalModal(true);
                    } else {
                        console.log('Could not extract approval request ID from response:', response.response);
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
            };

            setMessages(prev => [...prev, agentMessage]);
        } catch (error: any) {
            // Don't show error if request was aborted
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

        // Get cursor position
        const cursorPosition = e.target.selectionStart;
        const textBeforeCursor = value.substring(0, cursorPosition);

        // Check for command trigger (/)
        const commandMatch = textBeforeCursor.match(/\/(\w*)$/);
        if (commandMatch) {
            const query = '/' + commandMatch[1].toLowerCase();

            // Client-side command list with role-based access control
            const ALL_COMMANDS: CommandAutocompleteResult[] = [
                { command: '/email', description: 'Send emails or search inbox', category: 'communication', examples: '/email summary' },
                { command: '/search', description: 'Search knowledge base', category: 'general', examples: '/search mining' },
                { command: '/schedule', description: 'Check schedules or create meetings', category: 'meetings', examples: '/schedule meeting' },
                { command: '/draft', description: 'Draft documents or minutes', category: 'documents', examples: '/draft minutes' },
                { command: '/analyze', description: 'Analyze uploaded documents', category: 'analysis', examples: '/analyze report.pdf' },
                { command: '/broadcast', description: 'Broadcast message to all TWGs', category: 'communication', examples: '/broadcast unexpected delay', roles: ['admin', 'secretariat_lead'] }
            ];

            // Filter commands based on query and user role
            const filteredCommands = ALL_COMMANDS.filter(cmd => {
                const matchesQuery = cmd.command.toLowerCase().startsWith(query);
                const hasRole = !cmd.roles || (user?.role && cmd.roles.includes(user.role as any)); // Check if user has required role
                return matchesQuery && hasRole;
            });

            if (filteredCommands.length > 0) {
                setCommandSuggestions(filteredCommands);
                setAutocompleteType('command');
                setSelectedSuggestionIndex(0);
                return;
            }
        }

        // Check for mention trigger (@)
        const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
        if (mentionMatch) {
            const query = mentionMatch[1].toLowerCase();
            try {
                const twgs = await twgService.listTWGs();
                const filtered = twgs.filter((t: any) =>
                    t.name.toLowerCase().includes(query) ||
                    t.pillar?.toLowerCase().includes(query)
                ).map((t: any) => ({
                    mention: `@${t.name}`,
                    agent_id: t.id,
                    name: t.name,
                    icon: 'smart_toy',
                    description: t.pillar || 'Technical Working Group'
                }));

                setMentionSuggestions(filtered as any); // Type assertion to handle interface mismatch if any
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
        // Replace the partial command with the full command
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

            // Focus input and set cursor position
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
        // Replace the partial mention with the full mention
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

            // Focus input and set cursor position
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
        // Handle autocomplete navigation
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

        // Normal message send
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Clear conversation handler
    const handleClearConversation = () => {
        if (messages.length === 0 && !isLoading) return;

        if (window.confirm('Are you sure you want to clear this conversation? This action cannot be undone.')) {
            // Abort any ongoing request
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
                abortControllerRef.current = null;
            }

            // Clear state
            setMessages([]);
            setConversationId(undefined);
            setIsLoading(false);
        }
    };

    // Email approval handlers
    const handleApproveEmail = async (requestId: string, modifications?: EmailDraft) => {
        try {
            const approvalData = {
                request_id: requestId,
                approved: true,
                modifications: modifications || null
            };

            const result = await agentService.approveEmail(requestId, approvalData);

            // Close modal
            setShowApprovalModal(false);
            setPendingEmailApproval(null);

            // Add success message
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

            // Close modal
            setShowApprovalModal(false);
            setPendingEmailApproval(null);

            // Add decline message
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
        <>
            <div className="h-[calc(100vh-140px)] flex overflow-hidden">
                {/* Chat Area */}
                <div className="flex-1 flex flex-col bg-[#f6f6f8] dark:bg-[#0d121b]">
                    {/* Agent Header */}
                    <div className="bg-white dark:bg-[#1a202c] border-b border-[#e7ebf3] dark:border-[#2d3748] px-6 py-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div className="size-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white">
                                    <span className="material-symbols-outlined">smart_toy</span>
                                </div>
                                <span className="absolute bottom-0 right-0 size-3 border-2 border-white dark:border-[#1a202c] bg-green-500 rounded-full"></span>
                            </div>
                            <div>
                                <h3 className="font-bold text-[#0d121b] dark:text-white">{agentName}</h3>
                                <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                                    <span className="size-1.5 bg-green-500 rounded-full"></span>
                                    Online
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {isLoading && (
                                <button
                                    onClick={() => {
                                        if (abortControllerRef.current) {
                                            abortControllerRef.current.abort();
                                            abortControllerRef.current = null;
                                        }
                                        setIsLoading(false);
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
                                <div className="max-w-4xl w-full">
                                    <div className="text-center mb-12">
                                        <div className="size-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center backdrop-blur-sm">
                                            <span className="material-symbols-outlined text-blue-600 dark:text-blue-400" style={{ fontSize: '48px' }}>chat_bubble</span>
                                        </div>
                                        <h3 className="text-2xl font-semibold text-[#0d121b] dark:text-white mb-3">Welcome to ECOWAS Summit Assistant</h3>
                                        <p className="text-base text-[#6b7280] dark:text-[#9ca3af] max-w-xl mx-auto leading-relaxed">
                                            I'm here to help with TWG coordination, document drafting, and summit preparation. What can I assist you with today?
                                        </p>
                                    </div>

                                    {/* Available Commands */}
                                    <div className="mb-8">
                                        <h4 className="text-sm font-semibold text-[#0d121b] dark:text-white mb-4 flex items-center gap-2">
                                            <span className="material-symbols-outlined text-[20px] text-blue-600">terminal</span>
                                            Quick Commands
                                        </h4>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                            <div className="group bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-4 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md transition-all cursor-pointer">
                                                <div className="flex items-start gap-3">
                                                    <div className="size-10 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                                        <span className="material-symbols-outlined text-[20px] text-blue-600 dark:text-blue-400">email</span>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-semibold text-[#0d121b] dark:text-white font-mono mb-1">/email</div>
                                                        <div className="text-xs text-[#6b7280] dark:text-[#9ca3af] leading-relaxed">Send emails or search inbox</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="group bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-4 hover:border-purple-300 dark:hover:border-purple-600 hover:shadow-md transition-all cursor-pointer">
                                                <div className="flex items-start gap-3">
                                                    <div className="size-10 rounded-lg bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                                        <span className="material-symbols-outlined text-[20px] text-purple-600 dark:text-purple-400">search</span>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-semibold text-[#0d121b] dark:text-white font-mono mb-1">/search</div>
                                                        <div className="text-xs text-[#6b7280] dark:text-[#9ca3af] leading-relaxed">Search knowledge base</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="group bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-4 hover:border-green-300 dark:hover:border-green-600 hover:shadow-md transition-all cursor-pointer">
                                                <div className="flex items-start gap-3">
                                                    <div className="size-10 rounded-lg bg-green-50 dark:bg-green-900/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                                        <span className="material-symbols-outlined text-[20px] text-green-600 dark:text-green-400">event</span>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-semibold text-[#0d121b] dark:text-white font-mono mb-1">/schedule</div>
                                                        <div className="text-xs text-[#6b7280] dark:text-[#9ca3af] leading-relaxed">Check schedules or create meetings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="group bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-4 hover:border-orange-300 dark:hover:border-orange-600 hover:shadow-md transition-all cursor-pointer">
                                                <div className="flex items-start gap-3">
                                                    <div className="size-10 rounded-lg bg-orange-50 dark:bg-orange-900/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                                        <span className="material-symbols-outlined text-[20px] text-orange-600 dark:text-orange-400">description</span>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-semibold text-[#0d121b] dark:text-white font-mono mb-1">/draft</div>
                                                        <div className="text-xs text-[#6b7280] dark:text-[#9ca3af] leading-relaxed">Draft documents</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="group bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-4 hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-md transition-all cursor-pointer">
                                                <div className="flex items-start gap-3">
                                                    <div className="size-10 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                                        <span className="material-symbols-outlined text-[20px] text-indigo-600 dark:text-indigo-400">analytics</span>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-semibold text-[#0d121b] dark:text-white font-mono mb-1">/analyze</div>
                                                        <div className="text-xs text-[#6b7280] dark:text-[#9ca3af] leading-relaxed">Analyze documents or data</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="group bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-4 hover:border-pink-300 dark:hover:border-pink-600 hover:shadow-md transition-all cursor-pointer">
                                                <div className="flex items-start gap-3">
                                                    <div className="size-10 rounded-lg bg-pink-50 dark:bg-pink-900/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                                        <span className="material-symbols-outlined text-[20px] text-pink-600 dark:text-pink-400">campaign</span>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-semibold text-[#0d121b] dark:text-white font-mono mb-1">/broadcast</div>
                                                        <div className="text-xs text-[#6b7280] dark:text-[#9ca3af] leading-relaxed">Broadcast to all TWGs</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            messages.map((message) => (
                                <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                                    {message.role === 'agent' && (
                                        <div className="size-9 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md">
                                            <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                                        </div>
                                    )}
                                    <div className={`max-w-[75%] ${message.role === 'user' ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-lg' : 'bg-white dark:bg-[#1a202c] shadow-md border border-[#e7ebf3] dark:border-[#2d3748]'} rounded-2xl p-4`}>
                                        <div className={`text-sm leading-relaxed ${message.role === 'agent' ? 'text-[#0d121b] dark:text-white' : 'text-white'}`}>
                                            {message.role === 'agent' ? formatMarkdownText(message.content) : message.content}
                                        </div>
                                        {message.citations && message.citations.length > 0 && (
                                            <div className="mt-4 pt-3 border-t border-[#e7ebf3] dark:border-[#2d3748]">
                                                <div className="text-xs font-semibold text-[#6b7280] dark:text-[#9ca3af] mb-2 flex items-center gap-1">
                                                    <span className="material-symbols-outlined text-[14px]">library_books</span>
                                                    Sources
                                                </div>
                                                {message.citations.map((citation, idx) => (
                                                    <div key={idx} className="text-xs text-[#6b7280] dark:text-[#9ca3af] flex items-center gap-2 mb-1.5 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer">
                                                        <span className="material-symbols-outlined text-[14px]">article</span>
                                                        <span>{citation.source} (Page {citation.page})</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        <div className={`text-[10px] mt-2.5 ${message.role === 'user' ? 'text-white/70' : 'text-[#9ca3af]'}`}>
                                            {message.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>
                                    {message.role === 'user' && (
                                        <div className="size-9 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center shrink-0 shadow-md">
                                            <span className="material-symbols-outlined text-white text-[18px]">person</span>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        {isLoading && (
                            <div className="flex gap-3 justify-start animate-in fade-in duration-300">
                                <div className="size-9 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md">
                                    <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                                </div>
                                <div className="bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-2xl p-4 shadow-md">
                                    <div className="flex gap-1.5 items-center">
                                        <div className="size-2.5 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                        <div className="size-2.5 bg-purple-600 dark:bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                        <div className="size-2.5 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                    </div>
                                </div>
                            </div>
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

                        <div className="relative bg-white dark:bg-[#0d121b] border border-[#e7ebf3] dark:border-[#2d3748] rounded-2xl shadow-lg focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500 dark:focus-within:border-blue-400 transition-all">
                            {/* Command Autocomplete */}
                            {autocompleteType === 'command' && (commandSuggestions || []).length > 0 && (
                                <CommandAutocomplete
                                    suggestions={commandSuggestions}
                                    selectedIndex={selectedSuggestionIndex}
                                    onSelect={handleCommandSelect}
                                    onHover={setSelectedSuggestionIndex}
                                />
                            )}

                            {/* Mention Autocomplete */}
                            {autocompleteType === 'mention' && (mentionSuggestions || []).length > 0 && (
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

                {/* Email Approval Modal */}
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

                {/* Settings Modal */}
                {showSettingsModal && (
                    <SettingsModal
                        onClose={() => setShowSettingsModal(false)}
                    />
                )}
            </div>
        </>
    );
}
