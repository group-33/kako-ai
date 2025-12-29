import { MessageSquare, Settings, User, Trash2 } from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { cn } from "@/lib/utils";
import { Chat } from "@/components/Chat";

function App() {
  const { threads, activeThreadId, addThread, setActiveThread, deleteThread } = useChatStore();

  return (
    <div className="flex h-screen w-full bg-slate-50">
      {/* --- Linke Sidebar --- */}
      <aside className="w-64 bg-slate-950 text-slate-300 flex flex-col p-4 hidden md:flex border-r border-slate-900">
        <div className="font-bold text-white text-xl mb-8 pl-2 tracking-tight">Kako AI</div>

        <nav className="space-y-2 flex-1 overflow-y-auto pr-2">
          <button
            onClick={addThread}
            className="flex items-center gap-3 w-full px-3 py-2.5 bg-slate-800 text-white rounded-lg transition hover:bg-slate-700 shadow-sm mb-6"
          >
            <MessageSquare size={18} />
            <span className="font-medium text-sm">Neuer Chat</span>
          </button>

          <div className="text-[10px] font-bold text-slate-500 mb-2 px-2 uppercase tracking-wider">
            Verlauf
          </div>

          <div className="space-y-1">
            {threads.map((thread) => {
              const isActive = thread.id === activeThreadId;
              return (
                <div
                  key={thread.id}
                  className={cn(
                    "group flex items-center justify-between gap-3 w-full px-3 py-2 rounded-md text-sm transition-all cursor-pointer",
                    isActive
                      ? "bg-slate-800/80 text-white shadow-sm"
                      : "hover:bg-slate-800/50 text-slate-400 hover:text-slate-200"
                  )}
                  onClick={() => setActiveThread(thread.id)}
                >
                  <span className="truncate">{thread.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteThread(thread.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })}
          </div>
        </nav>

        <div className="mt-auto pt-4 border-t border-slate-800 space-y-1">
          <button className="flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm transition-colors">
            <Settings size={16} />
            <span>Einstellungen</span>
          </button>
          <button className="flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm transition-colors">
            <User size={16} />
            <span>Profil</span>
          </button>
        </div>
      </aside>

      {/* --- Hauptbereich --- */}
      <main className="flex-1 flex flex-col h-screen bg-slate-50">
        <div className="flex-1 p-2 md:p-6 overflow-hidden">
          <div className="mx-auto max-w-5xl h-full flex flex-col">
            {/* Key changes force re-mount of Chat, resetting mock state */}
            {activeThreadId ? (
              <Chat key={activeThreadId} />
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400">
                Wähle einen Chat aus oder starte einen neuen.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
