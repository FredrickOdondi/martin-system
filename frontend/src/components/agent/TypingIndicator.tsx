interface TypingIndicatorProps {
    agentName?: string;
    agentIcon?: string;
    message?: string;
}

export default function TypingIndicator({ agentName = 'AI Assistant', agentIcon, message }: TypingIndicatorProps) {
    return (
        <div className="flex gap-3 justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className={`size-9 rounded-full ${agentIcon || 'bg-gradient-to-br from-blue-600 to-purple-600'} flex items-center justify-center text-white shrink-0 shadow-md animate-pulse`}>
                <span className="material-symbols-outlined text-[20px]">smart_toy</span>
            </div>
            <div className="flex flex-col gap-1">
                {/* Agent name */}
                <div className="flex items-center gap-2 px-2">
                    <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">{agentName}</span>
                    <span className="text-[10px] text-blue-600 dark:text-blue-400 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                        typing
                    </span>
                </div>

                {/* Typing bubble */}
                <div className="bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-2xl rounded-tl-sm p-4 shadow-md">
                    {message ? (
                        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                            <div className="flex gap-1">
                                <div className="size-1.5 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="size-1.5 bg-purple-600 dark:bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="size-1.5 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                            <span className="italic">{message}</span>
                        </div>
                    ) : (
                        <div className="flex gap-1.5 items-center">
                            <div className="size-2.5 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="size-2.5 bg-purple-600 dark:bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="size-2.5 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
