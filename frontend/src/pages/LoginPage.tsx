import { useState } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { LegalModal } from "@/components/LegalModal";

export default function LoginPage() {
    const { signIn, signUp } = useAuthStore();
    const navigate = useNavigate();
    const { t } = useTranslation();

    const [isSignUp, setIsSignUp] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [showTerms, setShowTerms] = useState(false);
    const [showPrivacy, setShowPrivacy] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        if (!email || !password || (isSignUp && !name)) {
            setError(t('login.errorMissing'));
            setIsLoading(false);
            return;
        }

        try {
            if (isSignUp) {
                const { error } = await signUp(email, password, name);
                if (error) throw error;
                navigate("/");
            } else {
                const { error } = await signIn(email, password);
                if (error) throw error;
                navigate("/");
            }
        } catch (err: any) {
            setError(err.message || "Authentication failed");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative">

            
            <div className="absolute top-4 right-4 animate-in fade-in zoom-in duration-300 delay-100">
                <LanguageSwitcher />
            </div>

            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

                
                <div className="flex flex-col items-center mb-10">
                    <img
                        src="/kako_logo.jpg"
                        alt="Kako Elektro GmbH"
                        className="h-24 w-auto object-contain bg-white p-3 rounded-2xl shadow-lg mb-4"
                    />
                    <p className="text-slate-400 mt-2 text-sm text-center">{t('login.subtitle')}</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
                            {error}
                        </div>
                    )}

                    
                    {isSignUp && (
                        <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                            <label className="text-sm font-medium text-slate-300 ml-1">{t('login.name')}</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500/50 focus:border-slate-500 transition-all placeholder:text-slate-600"
                                placeholder={t('login.namePlaceholder')}
                                required
                            />
                        </div>
                    )}

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300 ml-1">{t('login.email')}</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500/50 focus:border-slate-500 transition-all placeholder:text-slate-600"
                            placeholder={t('login.emailPlaceholder')}
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <div className="flex justify-between items-center ml-1">
                            <label className="text-sm font-medium text-slate-300">{t('login.password')}</label>
                        </div>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500/50 focus:border-slate-500 transition-all placeholder:text-slate-600"
                            placeholder={t('login.passwordPlaceholder')}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className={cn(
                            "w-full bg-slate-100 hover:bg-white text-slate-900 font-semibold py-3.5 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2",
                            isLoading && "opacity-80 cursor-not-allowed"
                        )}
                    >
                        {isLoading ? (
                            <>
                                <Loader2 size={20} className="animate-spin" />
                                {isSignUp ? t('login.loadingSignUp') : t('login.loading')}
                            </>
                        ) : (
                            <>
                                {isSignUp ? t('login.createAccount') : t('login.signIn')}
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>

                    <div className="space-y-6 pt-2">
                        
                        <div className="text-center">
                            <p className="text-slate-400 text-sm">
                                {isSignUp ? t('login.hasAccount') : t('login.noAccount')}{" "}
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsSignUp(!isSignUp);
                                        setError("");
                                    }}
                                    className="text-white font-medium hover:underline transition-all"
                                >
                                    {isSignUp ? t('login.signIn') : t('login.signUp')}
                                </button>
                            </p>
                        </div>

                        
                        <div className="text-center border-t border-slate-800/50 pt-6">
                            <p className="text-slate-500 text-xs">
                                {t('login.termsPrefix')}
                                <button
                                    type="button"
                                    onClick={() => setShowTerms(true)}
                                    className="underline hover:text-slate-300 transition-colors"
                                >
                                    {t('login.termsLink')}
                                </button>
                                {t('login.termsAnd')}
                                <button
                                    type="button"
                                    onClick={() => setShowPrivacy(true)}
                                    className="underline hover:text-slate-300 transition-colors"
                                >
                                    {t('login.privacyLink')}
                                </button>
                                {t('login.termsSuffix')}
                            </p>
                        </div>
                    </div>
                </form>
            </div>

            <LegalModal
                isOpen={showTerms}
                onClose={() => setShowTerms(false)}
                title={t('legal.termsTitle')}
                content={t('legal.termsContent')}
                closeLabel={t('legal.close')}
            />

            <LegalModal
                isOpen={showPrivacy}
                onClose={() => setShowPrivacy(false)}
                title={t('legal.privacyTitle')}
                content={t('legal.privacyContent')}
                closeLabel={t('legal.close')}
            />
        </div>
    );
}
