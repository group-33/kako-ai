import { useState, useRef } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { User, LogOut, Save, Camera, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
    const { user, signOut, updateProfile, uploadAvatar, setAvatarUrl } = useAuthStore();
    const { t } = useTranslation();
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [name, setName] = useState(user?.user_metadata?.full_name || "");
    const [isEditing, setIsEditing] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const handleSave = async () => {
        await updateProfile(name);
        setIsEditing(false);
    };

    const handleSignOut = async () => {
        await signOut();
        navigate("/login", { replace: true });
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Immediate local preview
        const reader = new FileReader();
        reader.onload = (ev) => {
            if (ev.target?.result) {
                setAvatarUrl(ev.target.result as string);
            }
        };
        reader.readAsDataURL(file);

        setIsUploading(true);
        const { error } = await uploadAvatar(file);
        setIsUploading(false);

        if (error) {
            console.error("Upload failed", error);
            alert("Failed to upload avatar. Please ensure you have an 'avatars' storage bucket.");
        }
    };

    return (
        <div className="h-full overflow-y-auto p-8 relative z-0">
            <div className="max-w-2xl mx-auto space-y-8">

                <div>
                    <h1 className="text-3xl font-bold text-white">{t('profile.title')}</h1>
                    <p className="text-slate-400 mt-2">{t('profile.subtitle')}</p>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
                    <div className="px-6 py-8 flex flex-col items-center border-b border-slate-800 bg-slate-900/50">
                        <div className="relative group">
                            <div className="w-24 h-24 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-4 ring-4 ring-slate-950 shadow-sm overflow-hidden">
                                {user?.user_metadata?.avatar_url ? (
                                    <img
                                        src={user.user_metadata.avatar_url}
                                        alt="Profile"
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <User size={40} />
                                )}
                                {isUploading && (
                                    <div className="absolute inset-0 bg-slate-900/60 flex items-center justify-center">
                                        <Loader2 size={24} className="animate-spin text-white" />
                                    </div>
                                )}
                            </div>
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isUploading}
                                className="absolute bottom-4 right-0 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full p-2 shadow-lg transition-colors border-2 border-slate-900"
                            >
                                <Camera size={16} />
                            </button>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                accept="image/*"
                                onChange={handleFileChange}
                            />
                        </div>

                        <h2 className="text-xl font-bold text-white">{user?.user_metadata?.full_name || 'User'}</h2>
                        <p className="text-slate-400">{user?.email}</p>
                    </div>

                    <div className="p-6 space-y-6">
                        <div className="space-y-4">
                            <div className="grid gap-2">
                                <label className="text-sm font-medium text-slate-400">{t('profile.displayName')}</label>
                                <input
                                    type="text"
                                    value={name}
                                    disabled={!isEditing}
                                    onChange={(e) => setName(e.target.value)}
                                    className={cn(
                                        "w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all",
                                        isEditing
                                            ? "bg-slate-950 border-slate-700 text-white placeholder:text-slate-600"
                                            : "bg-slate-950/50 border-transparent text-slate-400"
                                    )}
                                />
                            </div>

                            <div className="grid gap-2 opacity-60">
                                <label className="text-sm font-medium text-slate-400">{t('profile.email')}</label>
                                <div className="w-full px-4 py-2 rounded-lg border border-slate-800 bg-slate-950/50 text-slate-500">
                                    {user?.email}
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                            {isEditing ? (
                                <>
                                    <button
                                        onClick={() => {
                                            setIsEditing(false);
                                            setName(user?.user_metadata?.full_name || "");
                                        }}
                                        className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
                                    >
                                        {t('profile.cancel')}
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-indigo-900/20"
                                    >
                                        <Save size={16} />
                                        {t('profile.save')}
                                    </button>
                                </>
                            ) : (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white text-sm font-medium rounded-lg transition-colors"
                                >
                                    {t('profile.edit')}
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                <div className="bg-red-950/10 rounded-xl border border-red-900/30 p-6 shadow-sm">
                    <h3 className="text-lg font-bold text-red-400 mb-4">{t('profile.dangerZone')}</h3>
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-red-200/60">
                            {t('profile.logoutDesc')}
                        </p>
                        <button
                            onClick={handleSignOut}
                            className="px-4 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
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
