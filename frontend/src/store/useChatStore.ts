import { create } from "zustand";
import { persist } from "zustand/middleware";
import { supabase } from "@/lib/supabase";

type Message = any; // We store the assistant-ui message objects directly

type Thread = {
    id: string;
    title: string;
    date: string;
    messages: Message[] | null;
};

type ChatStore = {
    threads: Thread[];
    activeThreadId: string | null;
    modelId: string;
    isLoading: boolean;

    // Actions
    fetchThreads: () => Promise<void>;
    addThread: (baseTitle?: string) => Promise<string | null>;
    deleteThread: (id: string) => Promise<void>;
    renameThread: (threadId: string, newTitle: string) => Promise<void>;
    updateThreadMessages: (threadId: string, messages: Message[]) => Promise<void>;

    // Actions for messages (typically handled by Assistant UI runtime, but we need to notify store or DB)
    // For now, we mainly sync the thread title and usage. Message persistence detailed in Chat.tsx often.
    // However, the previous store stored messages. We need to load them.
    loadMessagesForThread: (threadId: string) => Promise<void>;

    setActiveThread: (id: string) => void;
    setModelId: (id: string) => void;
};

export const useChatStore = create<ChatStore>()(
    persist(
        (set, get) => ({
            threads: [],
            activeThreadId: null,
            modelId: "gemini-2.5-flash",
            isLoading: false,

            fetchThreads: async () => {
                console.log("fetching threads start");
                set({ isLoading: true });
                const { data, error } = await supabase
                    .from('threads')
                    .select('*')
                    .order('updated_at', { ascending: false });

                console.log("supabase response:", { data, error });

                if (error) {
                    console.error('Error fetching threads:', error);
                    set({ isLoading: false });
                    return;
                }

                // Transform DB threads to Store threads
                const threads: Thread[] = data.map(t => ({
                    id: t.id,
                    title: t.title,
                    date: t.updated_at,
                    messages: null // null indicates "not loaded yet"
                }));

                console.log("mapped threads:", threads);
                set({ threads, isLoading: false });

                // If there is an active thread, or we need to set one
                const currentActive = get().activeThreadId;
                if (!currentActive && threads.length > 0) {
                    set({ activeThreadId: threads[0]?.id });
                }
            },

            loadMessagesForThread: async (threadId) => {
                if (!threadId) return;

                const { data, error } = await supabase
                    .from('messages')
                    .select('*')
                    .eq('thread_id', threadId)
                    .order('created_at', { ascending: true });

                if (error) {
                    console.error('Error loading messages:', error);
                    return;
                }

                // Convert DB messages back to assistant-ui format
                // Try to parse content as JSON (for tool calls/tables), fallback to string
                const messages: Message[] = data.map(m => {
                    let content = m.content;
                    try {
                        // Check if it looks like a JSON array or object
                        if (content.startsWith('[') || content.startsWith('{')) {
                            content = JSON.parse(m.content);
                        }
                    } catch (e) {
                        // Keep as plain text if parse fails
                        console.warn("Failed to parse message content, using as text", e);
                    }

                    return {
                        id: m.id,
                        role: m.role,
                        content: content,
                        createdAt: new Date(m.created_at),
                    };
                });

                set(state => ({
                    threads: state.threads.map(t =>
                        t.id === threadId ? { ...t, messages } : t
                    )
                }));
            },

            addThread: async (baseTitle = "New Chat") => {
                const newThreadId = crypto.randomUUID();
                // Optimistic update
                const newThread: Thread = {
                    id: newThreadId,
                    title: baseTitle,
                    date: new Date().toISOString(),
                    messages: []
                };

                set(state => ({
                    threads: [newThread, ...state.threads],
                    activeThreadId: newThreadId
                }));

                const { error } = await supabase
                    .from('threads')
                    .insert({
                        id: newThreadId,
                        title: baseTitle,
                        updated_at: new Date().toISOString()
                    });

                if (error) {
                    console.error('Error creating thread:', error);
                    // Revert optimistic update? For now just log.
                    return null;
                }
                return newThreadId;
            },

            updateThreadMessages: async (threadId: string, messages: Message[]) => {
                // Update local state immediately
                set((state) => ({
                    threads: state.threads.map((t) =>
                        t.id === threadId ? { ...t, messages, date: new Date().toISOString() } : t
                    ),
                }));

                // Sync to Supabase
                // We use upsert to handle both new messages and updates (streaming)
                // We map the assistant-ui messages to our DB schema
                const dbMessages = messages.map(m => {
                    // Serialize content to JSON string to preserve tool calls / arrays
                    let contentString = "";
                    if (typeof m.content === 'string') {
                        contentString = m.content;
                    } else {
                        // It's an array or object (Tool calls, etc.)
                        contentString = JSON.stringify(m.content);
                    }

                    return {
                        id: m.id,
                        thread_id: threadId,
                        role: m.role,
                        content: contentString,
                        created_at: m.createdAt instanceof Date ? m.createdAt.toISOString() : (m.createdAt || new Date().toISOString())
                    };
                });

                if (dbMessages.length === 0) return;

                const { error } = await supabase
                    .from('messages')
                    .upsert(dbMessages, { onConflict: 'id' });

                if (error) {
                    console.error('Error syncing messages:', error);
                }
            },

            deleteThread: async (id) => {
                set(state => {
                    const newThreads = state.threads.filter(t => t.id !== id);
                    let nextActive = state.activeThreadId;
                    if (state.activeThreadId === id) {
                        nextActive = newThreads.length > 0 ? (newThreads[0]?.id ?? null) : null;
                    }
                    return { threads: newThreads, activeThreadId: nextActive };
                });

                const { error } = await supabase
                    .from('threads')
                    .delete()
                    .eq('id', id);

                if (error) console.error('Error deleting thread:', error);
            },

            renameThread: async (threadId, newTitle) => {
                set(state => ({
                    threads: state.threads.map(t =>
                        t.id === threadId ? { ...t, title: newTitle } : t
                    )
                }));

                const { error } = await supabase
                    .from('threads')
                    .update({ title: newTitle })
                    .eq('id', threadId);

                if (error) console.error('Error renaming thread:', error);
            },

            setActiveThread: (id) => {
                set({ activeThreadId: id });
                // We should trigger loading messages here or in the component effect
                get().loadMessagesForThread(id);
            },

            setModelId: (id) => {
                set({ modelId: id });
            },
        }),
        {
            name: "kako-chat-storage",
            partialize: (state) => ({ modelId: state.modelId }), // Only persist modelId locally
        }
    )
);
