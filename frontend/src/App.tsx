import { Chat } from "@/components/Chat";
import { MessageSquare, Settings, User } from "lucide-react"; // Icons (kamen mit Shadcn)

function App() {
  return (
    <div className="flex h-screen w-full bg-slate-50">
      {/* --- Linke Sidebar (Dummy) --- */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col p-4 hidden md:flex">
        <div className="font-bold text-white text-xl mb-8 pl-2">Kako AI</div>

        <nav className="space-y-2 flex-1">
          <button className="flex items-center gap-3 w-full px-3 py-2 bg-slate-800 text-white rounded-md transition hover:bg-slate-700">
            <MessageSquare size={18} />
            <span>Neuer Chat</span>
          </button>
          <div className="text-xs font-semibold text-slate-500 mt-6 mb-2 px-2">
            HEUTE
          </div>
          <button className="flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm">
            Frontend Setup
          </button>
        </nav>

        <div className="mt-auto pt-4 border-t border-slate-800 space-y-2">
          <button className="flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm">
            <Settings size={18} />
            <span>Einstellungen</span>
          </button>
          <button className="flex items-center gap-3 w-full px-3 py-2 hover:bg-slate-800 rounded-md text-sm">
            <User size={18} />
            <span>Profil</span>
          </button>
        </div>
      </aside>

      {/* --- Hauptbereich --- */}
      <main className="flex-1 flex flex-col h-screen">
        <div className="flex-1 p-4 md:p-6 overflow-hidden">
          <div className="mx-auto max-w-4xl h-full">
            {/* Hier laden wir unseren Chat */}
            <Chat />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
