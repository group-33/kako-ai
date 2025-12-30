import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
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
import { useTranslation } from "react-i18next";

export default function Dashboard() {
    const navigate = useNavigate();
    const { threads, addThread } = useChatStore();
    const { user } = useAuthStore();
    const { t } = useTranslation();

    const handleCreateProject = () => {
        addThread();
        navigate("/chat"); // Navigate to the most recent (just added) thread
    };

    const recentThreads = threads.slice(0, 3);

    return (
        <div className="h-full overflow-y-auto p-8 relative z-0">
            <div className="max-w-6xl mx-auto space-y-10">

                {/* Header Section */}
                <div className="flex items-end justify-between">
                    <div>
                        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">{t('dashboard.welcome', { name: user?.name || 'Engineer' })}</h1>
                        <p className="text-lg text-slate-500 mt-2 font-medium">{t('dashboard.subheading')}</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-100/50 text-emerald-700 text-xs font-bold rounded-full border border-emerald-200">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            {t('dashboard.systemOperational')}
                        </div>
                    </div>
                </div>

                {/* Hero / Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <button
                        onClick={handleCreateProject}
                        className="group relative overflow-hidden p-8 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-300 text-left"
                    >
                        <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                            <UploadCloud size={120} className="text-indigo-600 rotate-12 transform translate-x-4 -translate-y-4" />
                        </div>
                        <div className="relative z-10">
                            <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                                <UploadCloud className="text-indigo-600" size={24} />
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 mb-2">{t('dashboard.quickActions.extractBom.title')}</h3>
                            <p className="text-slate-500 text-sm mb-6 max-w-sm leading-relaxed">
                                {t('dashboard.quickActions.extractBom.description')}
                            </p>
                            <div className="inline-flex items-center gap-2 text-indigo-600 font-semibold text-sm group-hover:gap-3 transition-all">
                                {t('dashboard.quickActions.extractBom.action')} <ArrowRight size={16} />
                            </div>
                        </div>
                    </button>

                    <button
                        onClick={() => navigate('/chat')}
                        className="group relative overflow-hidden p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 text-white shadow-lg hover:shadow-xl transition-all duration-300 text-left"
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
                            <div className="inline-flex items-center gap-2 text-white font-semibold text-sm group-hover:gap-3 transition-all">
                                {t('dashboard.quickActions.searchParts.action')} <ArrowRight size={16} />
                            </div>
                        </div>
                    </button>
                </div>

                {/* Metrics / Stats Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard icon={<FileText size={20} />} label={t('dashboard.stats.activeProjects')} value={threads.length.toString()} trend={t('dashboard.stats.weekTrend')} />
                    <StatCard icon={<Activity size={20} />} label={t('dashboard.stats.bomsProcessed')} value="12" trend={t('dashboard.stats.successRate')} />
                    <StatCard icon={<TrendingUp size={20} />} label={t('dashboard.stats.totalSavings')} value="€1,240" trend={t('dashboard.stats.viaOptimization')} />
                    <StatCard icon={<ShieldCheck size={20} />} label={t('dashboard.stats.compliance')} value="100%" trend={t('dashboard.stats.rohsVerified')} />
                </div>

                {/* Recent Activity Section */}
                <div>
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-slate-800">{t('dashboard.recentProjects.title')}</h2>
                        <button onClick={() => navigate('/chat')} className="text-indigo-600 text-sm font-semibold hover:text-indigo-700 transition-colors">
                            {t('dashboard.recentProjects.viewAll')}
                        </button>
                    </div>
                    <div className="grid grid-cols-1 gap-4">
                        {recentThreads.length > 0 ? (
                            recentThreads.map((thread) => (
                                <div
                                    key={thread.id}
                                    onClick={() => navigate(`/chat/${thread.id}`)}
                                    className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md hover:border-indigo-100 transition-all cursor-pointer group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center border border-slate-100 group-hover:bg-indigo-50 group-hover:border-indigo-100 transition-colors">
                                            <Clock className="text-slate-400 group-hover:text-indigo-500" size={18} />
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-slate-900 group-hover:text-indigo-700 transition-colors">{thread.title}</h4>
                                            <p className="text-xs text-slate-500">{t('dashboard.recentProjects.lastUpdated')} {new Date(thread.date).toLocaleDateString()}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-400 group-hover:text-indigo-500 transition-colors">
                                        <span className="text-xs font-medium">{t('dashboard.recentProjects.continue')}</span>
                                        <ArrowRight size={14} />
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                                <p className="text-slate-500">{t('dashboard.recentProjects.noActivity')}</p>
                                <button className="text-indigo-600 font-medium text-sm mt-2">{t('dashboard.recentProjects.startFirst')}</button>
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
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
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
