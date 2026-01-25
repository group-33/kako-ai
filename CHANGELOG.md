# Changelog

## [Unreleased] – Jan 24/25, 2026

### 🚀 **New Features**

#### **Industrial-Grade Agent Backend**
- **System Prompt**: Tightened with strict domain boundaries, refusal policy, and security directives against jailbreaking/injection.
- **Data Precedence**: Documented rule that user-confirmed data (e.g., edited BOMs) strictly overrides AI extraction results.
- **Tooling**: Removed legacy tools; agent now uses active model context with generalized "Toolbox" access.
  - **BOM Tool Cleanup**: Consolidated to a single `perform_bom_extraction` tool and tightened the BOM preprocessing flow.

#### **Context & Draft System**
- **Smart Drafts**: Quick Actions now immediately create threads with localized `initialDraft` context.
- **Persistence**: Drafts are saved per-thread and persist across navigation/reloads.
- **Auto-Titling**: First user message triggers intelligent background renaming.
- **Cleanup**: Automatic removal of empty/no-draft threads on navigation.

#### **Premium Profile & Configuration**
- **Design**: Improved configuration and profile pages with a consistent color block design.
- **Avatar Upload**: Added photo upload with local preview; Sidebar nav icon switches to Avatar and "Profile" label updates to Display Name.

#### **User Management & Legal**
- **Sign-Up Flow**: Added dedicated sign-up mode with name field and seamless toggle.
- **Legal Compliance**: Centralized **Legal Modal** with localized Terms of Service & Privacy Policy wired into Login.
- **Logout**: Sign-out now cleanly redirects to `/login`.

#### **Dynamic Dashboard**
- **Activity Indicators**: Added dynamic "Weekly Activity" strings computed from real-time `updated_at` data (`+X this week`).
- **View Control**: Smart "View All/Show Less" toggle for project lists.
- **Action Buttons**: Quick Action cards now trigger specific draft flows (BOM/Procurement).

### ⚡ **Improvements & Polish**

#### **Chat Experience**
- **Sticky Scroll**: Added smart sticky behavior (`overflow-anchor: none`) to keep view pinned while streaming without jumps.
- **Visuals**: Footer background is fully opaque and matches chat panel color (hides text scrolling behind).
- **Empty State**: Suggestions moved to composer footer; empty message list rendering fixed.
- **Draft Injection**: Improved placeholder selection behavior when injecting prompts.

#### **Sidebar & Navigation**
- **Layout**: KakoAI logo centered; "Your Chats" grouped into a dedicated scrollable panel.
- **Flow**: "New Chat" button navigates directly to the new thread.
- **Typography**: "Chats" renamed to "Your chats" / "Deine Chats" and positioned below New Chat.
- **Alignment**: Adjusted spacing and icon grid usage.

#### **Localization (i18n)**
- **Prompts**: New longer, directive draft prompts (EN/DE) for BOM + Procurement.
- **Strings**: comprehensive coverage including "Show Less", dynamic counts, and Legal terms.
- **Tools**: BOM table, procurement options, and cost analysis UI strings fully localized.

#### **Tooling Behavior**
- **BOM Extraction**:
    - **Smart Preprocessing**: Adjusted automatic rotation for portrait images.
    - **Reliability**: Upload path injection is language-agnostic; failures return 500s.
- **Model Selection**: Consistency updates for `model_id` in both JSON and multipart requests.
- **Attachments**:
    - **Previews**: Added data-URL preview fallback (especially for Safari) and download buttons.
    - **UI**: Fixed spinner colors in dark mode.

### 🛠 **Fixes & Maintenance**

- **Frontend Stability**: Handled all warnings and errors from linting for a clean build.
- **Backend Stability**: General cleanup of legacy components, optimizations, and reliability improvements.
- **Login UI**: Centered the login subtitle.
