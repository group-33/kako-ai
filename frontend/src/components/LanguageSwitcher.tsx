import { useTranslation } from 'react-i18next';
import { cn } from "@/lib/utils";

export function LanguageSwitcher() {
    const { i18n } = useTranslation();

    return (
        <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
            <button
                onClick={() => i18n.changeLanguage('en')}
                className={cn(
                    "flex-1 px-2 py-1 text-xs font-medium rounded-md transition-all",
                    i18n.language.startsWith('en')
                        ? "bg-slate-700 text-white shadow-sm"
                        : "text-slate-500 hover:text-slate-300"
                )}
            >
                EN
            </button>
            <button
                onClick={() => i18n.changeLanguage('de')}
                className={cn(
                    "flex-1 px-2 py-1 text-xs font-medium rounded-md transition-all",
                    i18n.language.startsWith('de')
                        ? "bg-slate-700 text-white shadow-sm"
                        : "text-slate-500 hover:text-slate-300"
                )}
            >
                DE
            </button>
        </div>
    );
}
