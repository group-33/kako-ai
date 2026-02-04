import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useState } from "react";
import {
    UploadCloud,
    ArrowRight,
    FileText,
    Clock,
    Activity,
    PackageSearch,
    TrendingUp,
    ShieldCheck
} from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { useAuthStore } from "@/store/useAuthStore";
import { useMetricsStore } from "@/store/useMetricsStore";
import { useTranslation } from "react-i18next";

export default function Dashboard() {
    const navigate = useNavigate();
    const { threads, addThread, setDraft } = useChatStore();
    const { user } = useAuthStore();
    const { bomIds, bomStats, procurementSpendEur, procurementOrdersByMonth, feasibilityChecks, feasibilityChecksByWeek } = useMetricsStore();
    const { t, i18n } = useTranslation();

    const handleAction = async (actionType: 'extract' | 'search') => {
        let initialMessage = "";

        if (actionType === 'extract') {
            initialMessage = t('dashboard.quickActions.extractBom.prompt');
        } else if (actionType === 'search') {
            initialMessage = t('dashboard.quickActions.searchParts.prompt');
        }

        const newThreadId = await addThread(t('layout.newChat'));
        if (!newThreadId) return;
        setDraft(newThreadId, initialMessage);
        navigate(`/chat/${newThreadId}`, { state: { initialDraft: initialMessage } });
    };
    const [showAllThreads, setShowAllThreads] = useState(false);
    const recentThreads = showAllThreads ? threads : threads.slice(0, 3);
    const canToggleThreads = threads.length > 3;

    const getWeekStart = () => {
        const now = new Date();
        const day = now.getDay(); // 0 = Sunday
        const diff = day === 0 ? -6 : 1 - day;
        const start = new Date(now);
        start.setDate(now.getDate() + diff);
        start.setHours(0, 0, 0, 0);
        return start;
    };
    const weekStart = getWeekStart();
    const weekKey = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, "0")}-${String(weekStart.getDate()).padStart(2, "0")}`;
    const feasibilityThisWeek = feasibilityChecksByWeek[weekKey] || 0;

    const bomsExtracted = Object.keys(bomIds).length;
    const { editedRowsTotal, rowsTotal } = Object.values(bomStats).reduce(
        (acc, stat) => {
            acc.editedRowsTotal += stat.editedRows;
            acc.rowsTotal += stat.totalRows;
            return acc;
        },
        { editedRowsTotal: 0, rowsTotal: 0 }
    );
    const rawAccuracy = rowsTotal > 0 ? (1 - editedRowsTotal / rowsTotal) * 100 : 100;
    const accuracy = Math.max(0, Math.min(100, rawAccuracy));
    const accuracyFormatter = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 1 });
    const accuracyDisplay = accuracyFormatter.format(accuracy);
    const currencyFormatter = new Intl.NumberFormat(i18n.language, {
        style: "currency",
        currency: "EUR",
        maximumFractionDigits: 0,
    });
    const spendDisplay = currencyFormatter.format(procurementSpendEur);
    const now = new Date();
    const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    const ordersThisMonth = procurementOrdersByMonth[monthKey] || 0;

    return (
        <div className="h-full overflow-y-auto p-8 relative z-0">
            <div className="max-w-6xl mx-auto space-y-10">

                <div className="flex items-end justify-between">
                    <div>
                        <h1 className="text-4xl font-extrabold text-white tracking-tight">{t('dashboard.welcome', { name: user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Engineer' })}</h1>
                        <p className="text-lg text-slate-400 mt-2 font-medium">{t('dashboard.subheading')}</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/20">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            {t('dashboard.systemOperational')}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <button
                        onClick={() => handleAction('extract')}
                        className="group relative overflow-hidden p-8 rounded-2xl bg-white border border-slate-800 shadow-sm hover:shadow-xl hover:border-slate-700 transition-all duration-300 text-left dark:bg-slate-900"
                        style={{
                            background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
                        }}
                    >
                        <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                            <UploadCloud size={120} className="text-white rotate-12 transform translate-x-4 -translate-y-4" />
                        </div>
                        <div className="relative z-10">
                            <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 backdrop-blur-sm">
                                <UploadCloud className="text-white" size={24} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{t('dashboard.quickActions.extractBom.title')}</h3>
                            <p className="text-slate-300/80 text-sm mb-6 max-w-sm leading-relaxed">
                                {t('dashboard.quickActions.extractBom.description')}
                            </p>
                            <div className="inline-flex items-center gap-2 text-blue-400 font-semibold text-sm group-hover:gap-3 transition-all">
                                {t('dashboard.quickActions.extractBom.action')} <ArrowRight size={16} />
                            </div>
                        </div>
                    </button>

                    <button
                        onClick={() => handleAction('search')}
                        className="group relative overflow-hidden p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 text-white shadow-lg hover:shadow-xl border border-slate-800 hover:border-slate-700 transition-all duration-300 text-left"
                    >
                        <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                            <PackageSearch size={120} className="text-white rotate-12 transform translate-x-4 -translate-y-4" />
                        </div>
                        <div className="relative z-10">
                            <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 backdrop-blur-sm">
                                <PackageSearch className="text-white" size={24} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{t('dashboard.quickActions.searchParts.title')}</h3>
                            <p className="text-slate-300/80 text-sm mb-6 max-w-sm leading-relaxed">
                                {t('dashboard.quickActions.searchParts.description')}
                            </p>
                            <div className="inline-flex items-center gap-2 text-blue-400 font-semibold text-sm group-hover:gap-3 transition-all">
                                {t('dashboard.quickActions.searchParts.action')} <ArrowRight size={16} />
                            </div>
                        </div>
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                        icon={<FileText size={20} />}
                        label={t('dashboard.stats.feasibilityChecks')}
                        value={feasibilityChecks.toString()}
                        trend={t('dashboard.stats.weekTrend', { count: feasibilityThisWeek })}
                    />
                    <StatCard
                        icon={<Activity size={20} />}
                        label={t('dashboard.stats.bomsProcessed')}
                        value={bomsExtracted.toString()}
                        trend={t('dashboard.stats.successRate', { value: accuracyDisplay })}
                    />
                    <StatCard
                        icon={<TrendingUp size={20} />}
                        label={t('dashboard.stats.procurementSpend')}
                        value={spendDisplay}
                        trend={t('dashboard.stats.procurementOrdersThisMonth', { count: ordersThisMonth })}
                    />
                    <StatCard icon={<ShieldCheck size={20} />} label={t('dashboard.stats.compliance')} value="100%" trend={t('dashboard.stats.rohsVerified')} />
                </div>

                <div>
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-white">{t('dashboard.recentProjects.title')}</h2>
                        {canToggleThreads ? (
                            <button
                                onClick={() => setShowAllThreads((prev) => !prev)}
                                className="text-blue-600 text-sm font-semibold hover:text-blue-700 transition-colors"
                            >
                                {showAllThreads
                                    ? t('dashboard.recentProjects.viewLess')
                                    : t('dashboard.recentProjects.viewAll')}
                            </button>
                        ) : null}
                    </div>
                    <div className="grid grid-cols-1 gap-4">
                        {recentThreads.length > 0 ? (
                            recentThreads.map((thread) => (
                                <div
                                    key={thread.id}
                                    onClick={() => navigate(`/chat/${thread.id}`)}
                                    className="flex items-center justify-between p-4 bg-zinc-800 rounded-xl border border-zinc-700 shadow-sm hover:bg-zinc-750 hover:border-zinc-600 transition-all cursor-pointer group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-zinc-900/50 flex items-center justify-center border border-zinc-700 group-hover:bg-zinc-800 group-hover:border-zinc-600 transition-colors">
                                            <Clock className="text-zinc-400 group-hover:text-blue-400" size={18} />
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors">{thread.title}</h4>
                                            <p className="text-xs text-zinc-400">{t('dashboard.recentProjects.lastUpdated')} {new Date(thread.date).toLocaleDateString()}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 text-zinc-500 group-hover:text-blue-400 transition-colors">
                                        <span className="text-xs font-medium">{t('dashboard.recentProjects.continue')}</span>
                                        <ArrowRight size={14} />
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                                <p className="text-slate-500">{t('dashboard.recentProjects.noActivity')}</p>
                                <button className="text-blue-600 font-medium text-sm mt-2">{t('dashboard.recentProjects.startFirst')}</button>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}

function StatCard({ icon, label, value, trend }: { icon: ReactNode, label: string, value: string, trend: string }) {
    return (
        <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-slate-100 text-slate-600 rounded-lg">
                    {icon}
                </div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</span>
            </div>
            <div>
                <div className="text-2xl font-bold text-slate-900">{value}</div>
                <div className="text-xs font-medium text-emerald-600 mt-1">{trend}</div>
            </div>
        </div>
    )
}
