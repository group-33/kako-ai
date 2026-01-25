# Kako AI - Frontend (MVP)

This is the frontend repository for **Kako AI**, a modern chat interface supporting "Generative UI"—allowing the AI to render interactive React components (like tables) alongside text.

## 🚀 Tech Stack

Built with modern web technologies:

- **Core:** [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/)
- **UI Library:** [Shadcn UI](https://ui.shadcn.com/) (Radix Primitives)
- **AI UI:** [Assistant UI](https://www.assistant-ui.com/)
- **State Management:** [Zustand](https://github.com/pmndrs/zustand) (with persistence)
- **Internationalization:** [i18next](https://www.i18next.com/) (English/German)
- **Icons:** [Lucide React](https://lucide.dev/)

## ✨ Key Features

### 🔐 Authentication & User Profile
- **Client-Side Auth:** Secure-feel login system (mocked for MVP) with persistent session.
- **Login Page:** Includes "Sign Up" toggle, legal links (Terms/Privacy), and immediate language switching.
- **Profile Management:** Edit display name/email and log out via the Profile page.
- **Protected Routes:** Automatic redirection to `/login` for unauthenticated access.

### 💬 Advanced Chat Capabilities
- **Generative UI:** Renders structured data (BOM Tables, Cost Analysis) as interactive components.
- **Chat Persistence:** History is automatically saved to `localStorage` and restored on reload.
- **Dynamic Naming:** New chats are automatically renamed based on the context of the first message (using the selected LLM).
- **Thread Isolation:** Robust state management ensures messages don't bleed between threads.
- **Localized Chat Config:** Supports localized naming sequences (e.g., "New Chat" vs "Neuer Chat").
- **Draft Workflows:** Dashboard quick actions open a new chat with a localized draft prompt for review before sending.
- **Draft Persistence:** Per-thread drafts are restored when you navigate back, and empty threads without drafts/messages are cleaned up.

### ⚙️ Configuration & Personalization
- **Model Selection:** Dynamic configuration page to switch between available LLMs (Gemini 2.5 Flash, Pro, etc.).
- **Dashboard:** Personalized greeting and localized statistics.
- **Localization:** Full English and German support across the entire app.

## 🛠️ Installation & Start

Ensure [Node.js](https://nodejs.org/) is installed.

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in Browser:**
   Go to http://localhost:5173

## 📂 Project Structure

```
frontend/
├── src/
│ ├── components/
│ │ ├── assistant-ui/   # Chat-specific UI (Bubbles, Composer)
│ │ ├── tools/          # Generative UI Components (BOMTable, CostAnalysis)
│ │ ├── ui/             # Shadcn Standard Components
│ │ └── Chat.tsx        # Main Chat Logic & Runtime Configuration
│ ├── lib/              # Utilities
│ ├── pages/            # Page Views (Login, Profile, Config, ChatPage)
│ ├── runtime/          # Backend Runtime (API connection + tool rendering)
│ ├── store/            # Zustand Stores (Auth, Chat)
│ ├── i18n.ts           # i18next bootstrap
│ ├── locales/          # Localization strings
│ ├── App.tsx           # Router & Layout
│ └── main.tsx          # Entry Point
└── vite.config.ts      # Vite Config
```
