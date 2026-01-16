import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, Cpu } from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { cn } from "@/lib/utils";

type ModelOption = {
    id: string;
    name: string;
    provider: string;
};

const BACKEND_BASE_URL =
    (import.meta as any).env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

export default function Configuration() {
    const { t } = useTranslation();
    const { modelId, setModelId } = useChatStore();
    const [models, setModels] = useState<ModelOption[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BACKEND_BASE_URL}/config/models`)
            .then((res) => res.json())
            .then((data) => {
                setModels(data.models);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch models", err);
                // Fallback if backend fetch fails
                setModels([
                    { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Google" }
                ]);
                setLoading(false);
            });
    }, []);

    return (
        <div className="h-full overflow-y-auto p-8 relative z-0">
            <div className="max-w-4xl mx-auto space-y-10">

                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">{t('config.title')}</h1>
                    <p className="text-slate-500 mt-2">{t('config.save')}</p>
                </div>

                {/* Model Selection */}
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                    <div className="flex items-start gap-4 mb-6">
                        <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                            <Cpu size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-slate-900">{t('config.modelSelection')}</h2>
                            <p className="text-slate-500 text-sm mt-1 max-w-2xl">{t('config.modelDesc')}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {models.map((model) => {
                            const isSelected = modelId === model.id;
                            return (
                                <button
                                    key={model.id}
                                    onClick={() => setModelId(model.id)}
                                    className={cn(
                                        "flex items-start gap-4 p-4 rounded-xl border-2 text-left transition-all relative overflow-hidden group",
                                        isSelected
                                            ? "border-indigo-600 bg-indigo-50/50"
                                            : "border-slate-100 hover:border-indigo-200 hover:bg-slate-50"
                                    )}
                                >
                                    {isSelected && (
                                        <div className="absolute top-0 right-0 p-1.5 bg-indigo-600 rounded-bl-xl">
                                            <Check size={14} className="text-white" />
                                        </div>
                                    )}

                                    <div className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold shrink-0",
                                        isSelected ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-500"
                                    )}>
                                        {model.provider === "Google" ? "G" : "O"}
                                    </div>

                                    <div>
                                        <h3 className={cn("font-bold", isSelected ? "text-indigo-900" : "text-slate-800")}>
                                            {model.name}
                                        </h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={cn(
                                                "text-xs px-2 py-0.5 rounded-full font-medium",
                                                model.provider === "Google" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
                                            )}>
                                                {model.provider}
                                            </span>
                                        </div>
                                    </div>
                                </button>
                            )
                        })}
                        {loading && (
                            <div className="col-span-2 text-center py-8 text-slate-400">Loading models...</div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
