import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import {
    LayoutDashboard,
    MessageSquare,
    Settings,
    User,
    Plus,
    Trash2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/store/useChatStore";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Layout() {
    const { threads, addThread, deleteThread, fetchThreads } = useChatStore();
    const navigate = useNavigate();
    const location = useLocation();
    const { t } = useTranslation();

    useEffect(() => {
        fetchThreads();
    }, [fetchThreads]);

    const handleNewChat = async () => {
        const newThreadId = await addThread(t('layout.newChat'));
        if (!newThreadId) return;
        navigate(`/chat/${newThreadId}`);
    };

    const handleDeleteThread = async (id: string) => {
        const isActive = location.pathname === `/chat/${id}`;
        await deleteThread(id);
        if (isActive) {
            navigate("/chat");
        }
    };

    return (
        <div className="flex h-screen w-full bg-slate-950 text-slate-200">
            <aside className="w-64 bg-slate-900 flex flex-col p-4 border-r border-slate-800 shadow-xl z-10">
                <div className="flex items-center justify-center mb-8 px-2">
                    <div className="flex items-center justify-center w-full">
                        <img
                            src="/kako_logo.jpg"
                            alt="Kako Elektro GmbH"
                            className="h-12 w-auto object-contain rounded bg-white p-1"
                        />
                    </div>
                </div>

                <nav className="space-y-1 flex-1 min-h-0 flex flex-col">
                    <div className="mb-2">
                        <NavLink
                            to="/"
                            className={({ isActive }) => cn(
                                "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200 group",
                                isActive ? "bg-slate-700 text-white shadow-lg shadow-black/20" : "hover:bg-slate-800/50 hover:text-white"
                            )}
                            end
                        >
                            <LayoutDashboard size={18} />
                            <span className="font-medium text-sm">{t('layout.dashboard')}</span>
                        </NavLink>
                    </div>

                    <button
                        onClick={handleNewChat}
                        className="flex items-center gap-3 w-full px-3 py-2.5 bg-slate-800/50 border border-slate-700/50 text-slate-300 rounded-lg transition hover:bg-slate-800 hover:border-slate-600 hover:text-white shadow-sm mb-4 group"
                    >
                        <Plus size={16} className="text-sky-400 group-hover:text-sky-300 transition-colors" />
                        <span className="font-medium text-sm">{t('layout.newChat')}</span>
                    </button>

                    <div className="flex items-center justify-between px-3 text-[10px] font-bold text-slate-500 mb-3 uppercase tracking-wider">
                        <span>{t('layout.chats')}</span>
                    </div>

                    <div className="space-y-1 flex-1 min-h-0 overflow-y-auto pr-2 custom-scrollbar rounded-xl bg-slate-800/40 border border-slate-800/70 px-2 py-2 mb-3">
                        {threads.map((thread) => {
                            return (
                                <NavLink
                                    key={thread.id}
                                    to={`/chat/${thread.id}`}
                                    className={({ isActive }) =>
                                        cn(
                                            "group flex items-center justify-between gap-3 w-full px-3 py-2 rounded-md text-sm transition-all cursor-pointer border border-transparent",
                                            isActive
                                                ? "bg-slate-800 text-white shadow-sm border-slate-700/50"
                                                : "hover:bg-slate-800/30 text-slate-400 hover:text-slate-200"
                                        )
                                    }
                                >
                                    <div className="flex items-center gap-3 overflow-hidden">
                                        <MessageSquare size={14} className="shrink-0 opacity-70" />
                                        <span className="truncate">{thread.title}</span>
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            handleDeleteThread(thread.id);
                                        }}
                                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                                    >
                                        <Trash2 size={12} />
                                    </button>
                                </NavLink>
                            );
                        })}
                    </div>
                </nav>

                <div className="mt-auto pt-3 border-t border-slate-800 space-y-4 mt-3">
                    <div className="space-y-1">
                        <NavLink
                            to="/config"
                            className={({ isActive }) => cn(
                                "flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm transition-colors group",
                                isActive ? "bg-slate-800 text-slate-200" : "text-slate-400 group-hover:text-slate-200"
                            )}
                        >
                            <Settings size={16} className="text-slate-500 group-hover:text-slate-400" />
                            <span>{t('layout.configuration')}</span>
                        </NavLink>
                        <NavLink
                            to="/profile"
                            className={({ isActive }) => cn(
                                "flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm transition-colors group",
                                isActive ? "bg-slate-800 text-slate-200" : "text-slate-400 group-hover:text-slate-200"
                            )}
                        >
                            <User size={16} className="text-slate-500 group-hover:text-slate-400" />
                            <span>{t('layout.profile')}</span>
                        </NavLink>
                    </div>

                    <div className="px-3">
                        <LanguageSwitcher />
                    </div>
                </div>
            </aside>

            <main className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 relative">
                <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-slate-900/50 to-transparent pointer-events-none" />
                <Outlet />
            </main>
        </div>
    );
}
