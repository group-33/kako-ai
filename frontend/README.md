# Kako AI - Frontend (MVP)

Dies ist das Frontend-Repository für **Kako AI**. Es handelt sich um eine moderne Chat-Schnittstelle, die "Generative UI" unterstützt – das bedeutet, die KI kann nicht nur Text antworten, sondern interaktive React-Komponenten (wie Tabellen) rendern.

## 🚀 Tech Stack

Das Projekt basiert auf modernsten Web-Technologien:

- **Core:** [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool:** [Vite](https://vitejs.dev/) (Blitzschneller Dev-Server)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/)
- **UI Library:** [Shadcn UI](https://ui.shadcn.com/) (Radix Primitives)
- **AI UI:** [Assistant UI](https://www.assistant-ui.com/) (Chat Threads, Streaming)
- **Icons:** [Lucide React](https://lucide.dev/)

## ✨ Aktuelle Features

- **Modernes Chat-Interface:** Responsives Layout mit Sidebar und Chat-Bereich.
- **Generative UI / Tool Use:** Der Agent kann entscheiden, strukturierte Daten zu senden, die als Frontend-Komponenten gerendert werden (Beispiel: `PriceTableTool`).
- **Mock Runtime:** Aktuell läuft das Frontend mit einer lokalen Simulation (`useLocalRuntime`), um Streaming-Antworten und UI-Tools zu testen, ohne dass das Backend laufen muss.
- **Tailwind v4 Setup:** Optimiertes CSS-Loading ohne große Config-Dateien.

## 🛠️ Installation & Start

Stelle sicher, dass du [Node.js](https://nodejs.org/) installiert hast.

1. **In den Frontend-Ordner wechseln:**
   cd frontend

2. **Abhängigkeiten installieren:**
   npm install

3. **Entwicklungsserver starten:**
   npm run dev

4. **Im Browser öffnen:**
   Gehe auf http://localhost:5173

📂 Projektstruktur
Ein kurzer Überblick über die wichtigsten Ordner:

frontend/
├── src/
│ ├── components/
│ │ ├── assistant-ui/ # Chat-spezifische UI (Bubbles, Composer, etc.)
│ │ ├── tools/ # Generative UI Komponenten (z.B. PriceTableTool)
│ │ ├── ui/ # Shadcn Standard-Komponenten (Buttons, Cards)
│ │ └── Chat.tsx # Haupt-Chat-Logik & Mock Runtime
│ ├── lib/ # Hilfsfunktionen (utils.ts)
│ ├── App.tsx # Hauptlayout (Sidebar + Main Area)
│ ├── index.css # Tailwind Imports
│ └── main.tsx # Entry Point
├── package.json # Dependencies & Scripts
└── vite.config.ts # Vite Konfiguration (mit Path Alias @)

📝 Nächste Schritte
[ ] Verbindung zum Python (FastAPI) Backend herstellen.

[ ] useLocalRuntime durch echte API-Calls ersetzen.

[ ] Weitere Generative UI Tools hinzufügen.
