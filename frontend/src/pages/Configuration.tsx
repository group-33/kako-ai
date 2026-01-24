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
    (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
        .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

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
                setModels([
                    { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Google" }
                ]);
                setLoading(false);
            });
    }, []);

    return (
        <div className="h-full overflow-y-auto p-8 relative z-0">
            <div className="max-w-4xl mx-auto space-y-10">

                <div>
                    <h1 className="text-3xl font-bold text-white">{t('config.title')}</h1>
                    <p className="text-slate-400 mt-2">{t('config.save')}</p>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-sm">
                    <div className="flex items-start gap-4 mb-6">
                        <div className="w-10 h-10 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center shrink-0">
                            <Cpu size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-white">{t('config.modelSelection')}</h2>
                            <p className="text-slate-400 text-sm mt-1 max-w-2xl">{t('config.modelDesc')}</p>
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
                                            ? "border-indigo-500 bg-indigo-500/10"
                                            : "border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/50 bg-slate-950/30"
                                    )}
                                >
                                    {isSelected && (
                                        <div className="absolute top-0 right-0 p-1.5 bg-indigo-600 rounded-bl-xl">
                                            <Check size={14} className="text-white" />
                                        </div>
                                    )}

                                    <div className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold shrink-0",
                                        isSelected ? "bg-indigo-500/20 text-indigo-400" : "bg-slate-800 text-slate-500"
                                    )}>
                                        {model.provider === "Google" ? "G" : "O"}
                                    </div>

                                    <div>
                                        <h3 className={cn("font-bold", isSelected ? "text-indigo-400" : "text-slate-200")}>
                                            {model.name}
                                        </h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={cn(
                                                "text-xs px-2 py-0.5 rounded-full font-medium",
                                                model.provider === "Google" ? "bg-blue-500/10 text-blue-400" : "bg-green-500/10 text-green-400"
                                            )}>
                                                {model.provider}
                                            </span>
                                        </div>
                                    </div>
                                </button>
                            )
                        })}
                        {loading && (
                            <div className="col-span-2 text-center py-8 text-slate-500">Loading models...</div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
