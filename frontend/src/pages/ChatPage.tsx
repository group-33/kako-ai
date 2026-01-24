import { useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Chat } from "@/components/Chat";
import { useChatStore } from "@/store/useChatStore";

export default function ChatPage() {
    const { threadId } = useParams();
    const { threads, setActiveThread, activeThreadId, loadMessagesForThread, deleteThread, drafts, ensureThread } = useChatStore();
    const location = useLocation();
    const { t } = useTranslation();
    const threadsRef = useRef(threads);
    const draftsRef = useRef(drafts);
    const prevThreadIdRef = useRef<string | null>(null);
    const prevPathRef = useRef<string | null>(null);

    const initialDraft = location.state?.initialDraft as string | undefined;

    useEffect(() => {
        if (threadId) {
            const thread = threads.find(t => t.id === threadId);
            if (thread) {
                setActiveThread(threadId);
                // Trigger load if missing
                if (thread.messages === null) {
                    void loadMessagesForThread(threadId);
                }
            } else {
                ensureThread({
                    id: threadId,
                    title: t("layout.newChat"),
                    date: new Date().toISOString(),
                    messages: null,
                });
                void loadMessagesForThread(threadId);
            }
        }
    }, [threadId, threads, setActiveThread, loadMessagesForThread, ensureThread, t]);

    const effectiveId = threadId || activeThreadId;

    useEffect(() => {
        threadsRef.current = threads;
    }, [threads]);

    useEffect(() => {
        draftsRef.current = drafts;
    }, [drafts]);

    useEffect(() => {
        const prevThreadId = prevThreadIdRef.current;
        const prevPath = prevPathRef.current;

        if (prevThreadId) {
            const thread = threadsRef.current.find(t => t.id === prevThreadId);
            const isEmpty = thread && Array.isArray(thread.messages) && thread.messages.length === 0;
            const hasDraft = Boolean(drafts[prevThreadId]?.trim());
            const threadChanged = prevThreadId !== effectiveId;
            const pathChanged = prevPath !== null && prevPath !== location.pathname;
            if (isEmpty && !hasDraft && (threadChanged || pathChanged)) {
                void deleteThread(prevThreadId);
            }
        }

        prevThreadIdRef.current = effectiveId ?? null;
        prevPathRef.current = location.pathname;
    }, [effectiveId, location.pathname, deleteThread, drafts]);

    useEffect(() => {
        return () => {
            const currentId = effectiveId;
            if (!currentId) return;
            const thread = threadsRef.current.find(t => t.id === currentId);
            const isEmpty = thread && Array.isArray(thread.messages) && thread.messages.length === 0;
            const hasDraft = Boolean(draftsRef.current[currentId]?.trim());
            if (isEmpty && !hasDraft) {
                void deleteThread(currentId);
            }
        };
    }, [effectiveId, deleteThread]);

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
                <Chat key={effectiveId} threadId={effectiveId} initialDraft={initialDraft} />
            </div>
        </div>
    );
}
