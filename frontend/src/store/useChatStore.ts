import { create } from "zustand";
import { persist } from "zustand/middleware";

type Message = any; // We store the assistant-ui message objects directly

type Thread = {
    id: string;
    title: string;
    date: string;
    messages: Message[];
};

type ChatStore = {
    threads: Thread[];
    activeThreadId: string | null;
    modelId: string;
    addThread: (baseTitle?: string) => void;
    updateThreadMessages: (threadId: string, messages: Message[]) => void;
    renameThread: (threadId: string, newTitle: string) => void;
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
                    title: "New Chat",
                    date: new Date().toISOString(),
                    messages: [],
                },
            ],
            activeThreadId: "default",
            modelId: "gemini-2.5-flash",

            addThread: (baseTitle = "New Chat") => {
                set((state) => {
                    // Generate unique title
                    let title = baseTitle;
                    let counter = 1;
                    const existingTitles = new Set(state.threads.map((t) => t.title));

                    while (existingTitles.has(title)) {
                        counter++;
                        title = `${baseTitle} ${counter}`;
                    }

                    const newId = crypto.randomUUID();
                    const newThread = {
                        id: newId,
                        title: title,
                        date: new Date().toISOString(),
                        messages: [],
                    };

                    return {
                        threads: [newThread, ...state.threads],
                        activeThreadId: newId,
                    };
                });
            },

            updateThreadMessages: (threadId, messages) => {
                set((state) => ({
                    threads: state.threads.map((t) =>
                        t.id === threadId ? { ...t, messages, date: new Date().toISOString() } : t
                    ),
                }));
            },

            renameThread: (threadId, newTitle) => {
                set((state) => ({
                    threads: state.threads.map((t) =>
                        t.id === threadId ? { ...t, title: newTitle } : t
                    ),
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
            partialize: (state) => ({ threads: state.threads, modelId: state.modelId }),
        }
    )
);
