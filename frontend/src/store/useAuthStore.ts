import { create } from "zustand";
import { supabase } from "@/lib/supabase";
import { User } from "@supabase/supabase-js";

type AuthStore = {
    user: User | null;
    loading: boolean;
    signIn: (email: string, password: string) => Promise<{ error: any }>;
    signUp: (email: string, password: string, name: string) => Promise<{ error: any }>;
    signOut: () => Promise<{ error: any }>;
    updateProfile: (name: string) => Promise<{ error: any }>;
};

export const useAuthStore = create<AuthStore>((_set) => ({
    user: null,
    loading: true,

    signIn: async (email, password) => {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        return { error };
    },

    signUp: async (email, password, name) => {
        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: name
                }
            }
        });
        return { error };
    },

    signOut: async () => {
        const { error } = await supabase.auth.signOut();
        return { error };
    },

    updateProfile: async (name: string) => {
        const { error } = await supabase.auth.updateUser({
            data: { full_name: name }
        });
        return { error };
    },
}));
supabase.auth.getSession().then(({ data: { session } }) => {
    useAuthStore.setState({ user: session?.user ?? null, loading: false });
});

supabase.auth.onAuthStateChange((_event, session) => {
    useAuthStore.setState({ user: session?.user ?? null, loading: false });
});
