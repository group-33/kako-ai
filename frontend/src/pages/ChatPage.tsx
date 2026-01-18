import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Chat } from "@/components/Chat";
import { useChatStore } from "@/store/useChatStore";

export default function ChatPage() {
    const { threadId } = useParams();
    const { threads, setActiveThread, activeThreadId, loadMessagesForThread } = useChatStore();
    const navigate = useNavigate();
    const { t } = useTranslation();

    useEffect(() => {
        if (threadId) {
            const thread = threads.find(t => t.id === threadId);
            if (thread) {
                setActiveThread(threadId);
                // Trigger load if missing
                if (thread.messages === null) {
                    loadMessagesForThread(threadId);
                }
            } else {
                // If threads are still loading (threads array empty but isLoading true), wait? 
                // But typically threads loaded in Layout.
                // If thread in URL doesn't exist (e.g. deleted), redirect to main chat view
                if (threads.length > 0) navigate("/chat"); // Only redirect if we are sure we have loaded threads
            }
        }
    }, [threadId, threads, setActiveThread, navigate, loadMessagesForThread]);

    const effectiveId = threadId || activeThreadId;

    // Find the thread to check loading state
    const currentThread = threads.find(t => t.id === effectiveId);

    // If thread exists but messages are null, we are loading
    if (currentThread && currentThread.messages === null) {
        return (
            <div className="flex h-full items-center justify-center bg-slate-950">
                <div className="text-slate-400 animate-pulse">Loading conversation...</div>
            </div>
        );
    }

    if (!effectiveId) {
        return <div className="flex bg-white items-center justify-center h-full text-slate-400">{t('chatPage.selectPlaceholder')}</div>;
    }

    return (
        <div className="h-full p-2 md:p-6">
            <div className="mx-auto max-w-5xl h-full flex flex-col">
                <Chat key={effectiveId} threadId={effectiveId} />
            </div>
        </div>
    );
}
