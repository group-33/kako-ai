import { create } from "zustand";
import { persist } from "zustand/middleware";

type Thread = {
    id: string;
    title: string;
    date: string;
};

type ChatStore = {
    threads: Thread[];
    activeThreadId: string | null;
    modelId: string;
    addThread: () => void;
    setActiveThread: (id: string) => void;
    deleteThread: (id: string) => void;
    setModelId: (id: string) => void;
};

export const useChatStore = create<ChatStore>()(
    persist(
        (set) => ({
            threads: [
                {
                    id: "default",
                    title: "Neuer Chat",
                    date: new Date().toISOString(),
                },
            ],
            activeThreadId: "default",
            modelId: "gemini-2.5-flash",

            addThread: () => {
                const newId = crypto.randomUUID();
                const newThread = {
                    id: newId,
                    title: "Neuer Chat",
                    date: new Date().toISOString(),
                };
                set((state) => ({
                    threads: [newThread, ...state.threads],
                    activeThreadId: newId,
                }));
            },

            setActiveThread: (id) => {
                set({ activeThreadId: id });
            },

            deleteThread: (id) => {
                set((state) => {
                    const newThreads = state.threads.filter((t) => t.id !== id);
                    // If we deleted the active thread, switch to the first one available or null
                    let nextActive = state.activeThreadId;
                    if (state.activeThreadId === id) {
                        nextActive = newThreads.length > 0 && newThreads[0] ? newThreads[0].id : null;
                    }
                    return {
                        threads: newThreads,
                        activeThreadId: nextActive,
                    };
                });
            },

            setModelId: (id) => {
                set({ modelId: id });
            },
        }),
        {
            name: "kako-chat-storage",
            partialize: (state) => ({ threads: state.threads, modelId: state.modelId }), // Don't persist activeThreadId necessarily, or do? Let's just persist threads and config.
        }
    )
);
