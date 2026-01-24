import { useState } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { User, LogOut, Save } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
    const { user, signOut, updateProfile } = useAuthStore();
    const { t } = useTranslation();
    const navigate = useNavigate();

    const [name, setName] = useState(user?.user_metadata?.full_name || "");
    const [isEditing, setIsEditing] = useState(false);

    const handleSave = async () => {
        await updateProfile(name);
        setIsEditing(false);
    };
    const handleSignOut = async () => {
        await signOut();
        navigate("/login", { replace: true });
    };

    return (
        <div className="h-full overflow-y-auto p-8 relative z-0">
            <div className="max-w-2xl mx-auto space-y-8">

                <div>
                    <h1 className="text-3xl font-bold text-white">{t('profile.title')}</h1>
                    <p className="text-slate-400 mt-2">{t('profile.subtitle')}</p>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="px-6 py-8 flex flex-col items-center border-b border-slate-100 bg-slate-50/50">
                        <div className="w-24 h-24 rounded-full bg-slate-200 flex items-center justify-center text-slate-400 mb-4 ring-4 ring-white shadow-sm">
                            <User size={40} />
                        </div>
                        <h2 className="text-xl font-bold text-slate-900">{user?.user_metadata?.full_name || 'User'}</h2>
                        <p className="text-slate-500">{user?.email}</p>
                    </div>

                    <div className="p-6 space-y-6">
                        <div className="space-y-4">
                            <div className="grid gap-2">
                                <label className="text-sm font-medium text-slate-700">{t('profile.displayName')}</label>
                                <input
                                    type="text"
                                    value={name}
                                    disabled={!isEditing}
                                    onChange={(e) => setName(e.target.value)}
                                    className={cn(
                                        "w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all",
                                        isEditing ? "bg-white border-slate-300" : "bg-slate-50 border-transparent text-slate-600"
                                    )}
                                />
                            </div>

                            <div className="grid gap-2 opacity-60">
                                <label className="text-sm font-medium text-slate-700">{t('profile.email')}</label>
                                <div className="w-full px-4 py-2 rounded-lg border border-transparent bg-slate-50 text-slate-500">
                                    {user?.email}
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                            {isEditing ? (
                                <>
                                    <button
                                        onClick={() => {
                                            setIsEditing(false);
                                            setName(user?.user_metadata?.full_name || "");
                                        }}
                                        className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                                    >
                                        {t('profile.cancel')}
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-sm shadow-indigo-500/20"
                                    >
                                        <Save size={16} />
                                        {t('profile.save')}
                                    </button>
                                </>
                            ) : (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="px-4 py-2 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-sm font-medium rounded-lg transition-colors"
                                >
                                    {t('profile.edit')}
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl border border-red-100 p-6 shadow-sm">
                    <h3 className="text-lg font-bold text-slate-900 mb-4">{t('profile.dangerZone')}</h3>
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-slate-500">
                            {t('profile.logoutDesc')}
                        </p>
                        <button
                            onClick={handleSignOut}
                            className="px-4 py-2 bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                        >
                            <LogOut size={16} />
                            {t('profile.logout')}
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}
