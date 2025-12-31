import { Outlet, NavLink, useNavigate } from "react-router-dom";
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
    const { threads, addThread, deleteThread } = useChatStore();
    const navigate = useNavigate();
    const { t } = useTranslation();

    const handleNewChat = () => {
        addThread(t('layout.newChat'));
        navigate("/chat");
    };

    return (
        <div className="flex h-screen w-full bg-slate-50">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-950 text-slate-300 flex flex-col p-4 border-r border-slate-900 shadow-xl z-10">
                <div className="flex items-center justify-between mb-8 px-2">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                            K
                        </div>
                        <div className="font-bold text-white text-xl tracking-tight">Kako AI</div>
                    </div>
                </div>

                <nav className="space-y-1 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    <div className="mb-6">
                        <NavLink
                            to="/"
                            className={({ isActive }) => cn(
                                "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200 group",
                                isActive ? "bg-indigo-600 text-white shadow-lg shadow-indigo-900/20" : "hover:bg-slate-800/50 hover:text-white"
                            )}
                            end
                        >
                            <LayoutDashboard size={18} />
                            <span className="font-medium text-sm">{t('layout.dashboard')}</span>
                        </NavLink>
                    </div>

                    <div className="flex items-center justify-between px-3 text-[10px] font-bold text-slate-500 mb-2 uppercase tracking-wider">
                        <span>{t('layout.chats')}</span>
                    </div>

                    <button
                        onClick={handleNewChat}
                        className="flex items-center gap-3 w-full px-3 py-2.5 bg-slate-900/50 border border-slate-800 text-slate-200 rounded-lg transition hover:bg-slate-800 hover:border-slate-700 hover:text-white shadow-sm mb-4 group"
                    >
                        <Plus size={16} className="text-indigo-400 group-hover:text-indigo-300 transition-colors" />
                        <span className="font-medium text-sm">{t('layout.newChat')}</span>
                    </button>

                    <div className="space-y-1">
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
                                                : "hover:bg-slate-800/50 text-slate-400 hover:text-slate-200"
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
                                            deleteThread(thread.id);
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

                <div className="mt-auto pt-4 border-t border-slate-800/50 space-y-4">
                    <div className="space-y-1">
                        <NavLink
                            to="/config"
                            className={({ isActive }) => cn(
                                "flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm transition-colors group",
                                isActive ? "bg-slate-800 text-slate-200" : "text-slate-300"
                            )}
                        >
                            <Settings size={16} className="text-slate-500 group-hover:text-slate-300" />
                            <span>{t('layout.configuration')}</span>
                        </NavLink>
                        <NavLink
                            to="/profile"
                            className={({ isActive }) => cn(
                                "flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm transition-colors group",
                                isActive ? "bg-slate-800 text-slate-200" : "text-slate-300"
                            )}
                        >
                            <User size={16} className="text-slate-500 group-hover:text-slate-300" />
                            <span>{t('layout.profile')}</span>
                        </NavLink>
                    </div>

                    <div className="px-3">
                        <LanguageSwitcher />
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50 relative">
                <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-indigo-50/50 to-transparent pointer-events-none" />
                <Outlet />
            </main>
        </div>
    );
}
