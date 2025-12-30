import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Chat } from "@/components/Chat";
import { useChatStore } from "@/store/useChatStore";

export default function ChatPage() {
    const { threadId } = useParams();
    const { threads, setActiveThread, activeThreadId } = useChatStore();
    const navigate = useNavigate();

    useEffect(() => {
        if (threadId) {
            const exists = threads.some(t => t.id === threadId);
            if (exists) {
                setActiveThread(threadId);
            } else {
                // If thread in URL doesn't exist (e.g. deleted), redirect to main chat view
                navigate("/chat");
            }
        }
    }, [threadId, threads, setActiveThread, navigate]);

    const effectiveId = threadId || activeThreadId;

    if (!effectiveId) {
        return <div className="flex bg-white items-center justify-center h-full text-slate-400">Select a chat or start a new one.</div>;
    }

    return (
        <div className="h-full p-2 md:p-6">
            <div className="mx-auto max-w-5xl h-full flex flex-col">
                <Chat key={effectiveId} />
            </div>
        </div>
    );
}
