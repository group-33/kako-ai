import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ThreadMessageLike } from "@assistant-ui/react";
import { supabase } from "@/lib/supabase";

type Message = ThreadMessageLike;

type Thread = {
    id: string;
    title: string;
    date: string;
    messages: ReadonlyArray<Message> | null;
};

export type ChatStore = {
    threads: Thread[];
    activeThreadId: string | null;
    modelId: string;
    isLoading: boolean;
    drafts: Record<string, string>;

    // Actions
    fetchThreads: () => Promise<void>;
    addThread: (baseTitle?: string) => Promise<string | null>;
    deleteThread: (id: string) => Promise<void>;
    renameThread: (threadId: string, newTitle: string) => Promise<void>;
    updateThreadMessages: (threadId: string, messages: ReadonlyArray<Message>) => Promise<void>;
    setDraft: (threadId: string, draft: string) => void;
    clearDraft: (threadId: string) => void;
    ensureThread: (thread: Thread) => void;

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
            drafts: {},

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
                const dbThreads: Thread[] = data.map(t => ({
                    id: t.id,
                    title: t.title,
                    date: t.updated_at,
                    messages: null // null indicates "not loaded yet"
                }));

                const threadIds = dbThreads.map(t => t.id);
                const defaultTitles = new Set(["New Chat", "Neuer Chat"]);
                let threadsWithMessages = new Set<string>();

                if (threadIds.length > 0) {
                    const { data: messageRows, error: messageError } = await supabase
                        .from('messages')
                        .select('thread_id')
                        .in('thread_id', threadIds);

                    if (!messageError && messageRows) {
                        threadsWithMessages = new Set(messageRows.map(row => row.thread_id));
                    }
                }

                const emptyDefaultThreads = dbThreads.filter(t =>
                    defaultTitles.has(t.title) && !threadsWithMessages.has(t.id)
                );

                if (emptyDefaultThreads.length > 0) {
                    const deleteIds = emptyDefaultThreads.map(t => t.id);
                    supabase.from('threads').delete().in('id', deleteIds);
                }

                const filteredDbThreads = dbThreads.filter(t => !emptyDefaultThreads.some(e => e.id === t.id));

                const existingThreads = get().threads;
                const dbIds = new Set(filteredDbThreads.map(t => t.id));
                const nowMs = Date.now();
                const keepLocalThreads = existingThreads.filter((thread) => {
                    if (dbIds.has(thread.id)) return false;
                    if (Array.isArray(thread.messages) && thread.messages.length > 0) return true;
                    const createdAt = Date.parse(thread.date);
                    if (!Number.isNaN(createdAt)) {
                        const ageMs = nowMs - createdAt;
                        return ageMs < 5 * 60 * 1000;
                    }
                    return false;
                });

                const threads = [...filteredDbThreads, ...keepLocalThreads];

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
                const messages: Message[] = data.map((m) => {
                    let content: Message["content"] = m.content ?? "";
                    try {
                        if (typeof content === "string" && (content.startsWith("[") || content.startsWith("{"))) {
                            content = JSON.parse(content);
                        }
                    } catch (error) {
                        console.warn("Failed to parse message content, using as text", error);
                    }

                    return {
                        id: m.id,
                        role: m.role,
                        content,
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

            updateThreadMessages: async (threadId: string, messages: ReadonlyArray<Message>) => {
                // Update local state immediately
                set((state) => ({
                    threads: state.threads.map((t) =>
                        t.id === threadId
                            ? { ...t, messages: Array.from(messages), date: new Date().toISOString() }
                            : t
                    ),
                }));

                // Sync to Supabase
                // We use upsert to handle both new messages and updates (streaming)
                // We map the assistant-ui messages to our DB schema
                const dbMessages = messages.map((m) => {
                    const contentString =
                        typeof m.content === "string"
                            ? m.content
                            : JSON.stringify(m.content);

                    return {
                        id: m.id,
                        thread_id: threadId,
                        role: m.role,
                        content: contentString,
                        created_at: m.createdAt?.toISOString() ?? new Date().toISOString()
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

            setDraft: (threadId: string, draft: string) => {
                set((state) => ({
                    drafts: { ...state.drafts, [threadId]: draft }
                }));
            },

            clearDraft: (threadId: string) => {
                set((state) => {
                    const nextDrafts = { ...state.drafts };
                    delete nextDrafts[threadId];
                    return { drafts: nextDrafts };
                });
            },

            ensureThread: (thread: Thread) => {
                set((state) => {
                    if (state.threads.some((t) => t.id === thread.id)) return state;
                    return { threads: [thread, ...state.threads] };
                });
            },

            deleteThread: async (id) => {
                set(state => {
                    const newThreads = state.threads.filter(t => t.id !== id);
                    let nextActive = state.activeThreadId;
                    if (state.activeThreadId === id) {
                        nextActive = newThreads.length > 0 ? (newThreads[0]?.id ?? null) : null;
                    }
                    const nextDrafts = { ...state.drafts };
                    delete nextDrafts[id];
                    return { threads: newThreads, activeThreadId: nextActive, drafts: nextDrafts };
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
                void get().loadMessagesForThread(id);
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
