import { useState } from 'react';

interface TypingIndicatorProps {
    agentName?: string;
    agentIcon?: string;
    steps?: string[];
}

export default function TypingIndicator({ agentName = 'AI Assistant', agentIcon, steps = [] }: TypingIndicatorProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div className="flex gap-3 justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className={`size-9 rounded-full ${agentIcon || 'bg-gradient-to-br from-blue-600 to-purple-600'} flex items-center justify-center text-white shrink-0 shadow-md`}>
                <span className="material-symbols-outlined text-[20px] animate-pulse">smart_toy</span>
            </div>

            <div className="flex flex-col gap-1 max-w-[80%]">
                {/* Thinking Accordion */}
                <div className="bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl shadow-sm overflow-hidden transition-all">
                    {/* Header/Trigger */}
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left"
                    >
                        <div className="flex items-center gap-2">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                            </span>
                            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                                Thinking...
                            </span>
                        </div>

                        <div className="flex-1" />

                        <span className={`material-symbols-outlined text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                            expand_more
                        </span>
                    </button>

                    {/* Expanded Content */}
                    {isExpanded && (
                        <div className="px-4 pb-4 pt-1 border-t border-slate-100 dark:border-slate-800 animate-in slide-in-from-top-1 duration-200">
                            <div className="text-xs text-slate-500 dark:text-slate-400 font-mono bg-slate-50 dark:bg-[#0d121b] p-3 rounded-lg mt-2">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="material-symbols-outlined text-[14px] text-blue-500">bolt</span>
                                    <span className="font-semibold text-blue-600 dark:text-blue-400">Process Log</span>
                                </div>
                                <div className="space-y-1.5">
                                    <div className="flex items-center gap-2">
                                        <span className="text-green-500">✓</span>
                                        <span>Use agent: <span className="font-semibold">{agentName}</span></span>
                                    </div>
                                    {steps && steps.length > 0 ? (
                                        steps.map((step, i) => (
                                            <div key={i} className="flex items-start gap-2">
                                                <span className={i === steps.length - 1 ? "animate-pulse text-blue-500" : "text-green-500"}>
                                                    {i === steps.length - 1 ? "➜" : "✓"}
                                                </span>
                                                <span className={i === steps.length - 1 ? "font-medium" : "text-slate-500"}>{step}</span>
                                            </div>
                                        ))
                                    ) : (
                                        // Fallback default
                                        <div className="flex items-start gap-2">
                                            <span className="animate-pulse text-blue-500">➜</span>
                                            <span>Processing your request...</span>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2 opacity-50">
                                        <span className="typing-dots inline-flex gap-0.5">
                                            <span className="w-1 h-1 bg-current rounded-full animate-bounce"></span>
                                            <span className="w-1 h-1 bg-current rounded-full animate-bounce delay-100"></span>
                                            <span className="w-1 h-1 bg-current rounded-full animate-bounce delay-200"></span>
                                        </span>
                                        <span>Generating response...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

