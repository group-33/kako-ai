import { create } from "zustand";

type Thread = {
    id: string;
    title: string;
    date: Date;
};

type ChatStore = {
    threads: Thread[];
    activeThreadId: string | null;
    addThread: () => void;
    setActiveThread: (id: string) => void;
    deleteThread: (id: string) => void;
};

export const useChatStore = create<ChatStore>((set) => ({
    threads: [
        {
            id: "default",
            title: "Neuer Chat",
            date: new Date(),
        },
    ],
    activeThreadId: "default",

    addThread: () => {
        const newId = crypto.randomUUID();
        const newThread = {
            id: newId,
            title: "Neuer Chat",
            date: new Date(),
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
}));
