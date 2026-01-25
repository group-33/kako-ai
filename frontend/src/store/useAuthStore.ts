import { create } from "zustand";
import { supabase } from "@/lib/supabase";
import type { AuthError, User } from "@supabase/supabase-js";

type AuthStore = {
    user: User | null;
    loading: boolean;
    signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
    signUp: (email: string, password: string, name: string) => Promise<{ error: AuthError | null }>;
    signOut: () => Promise<{ error: AuthError | null }>;
    updateProfile: (name: string) => Promise<{ error: AuthError | null }>;
    uploadAvatar: (file: File) => Promise<{ error: AuthError | Error | null }>;
    setAvatarUrl: (url: string) => void;
};

export const useAuthStore = create<AuthStore>((set) => ({
    user: null,
    loading: true,

    setAvatarUrl: (url: string) => {
        set((state) => {
            if (!state.user) return state;
            return {
                user: {
                    ...state.user,
                    user_metadata: {
                        ...state.user.user_metadata,
                        avatar_url: url
                    }
                }
            };
        });
    },

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

    uploadAvatar: async (file: File) => {
        const fileExt = file.name.split('.').pop();
        const fileName = `${Math.random()}.${fileExt}`;
        const filePath = `${fileName}`;

        const { error: uploadError } = await supabase.storage
            .from('avatars')
            .upload(filePath, file);

        if (uploadError) return { error: uploadError };

        const { data } = supabase.storage.from('avatars').getPublicUrl(filePath);

        const { error: updateError } = await supabase.auth.updateUser({
            data: { avatar_url: data.publicUrl }
        });

        return { error: updateError };
    },
}));
supabase.auth.getSession().then(({ data: { session } }) => {
    useAuthStore.setState({ user: session?.user ?? null, loading: false });
});

supabase.auth.onAuthStateChange((_event, session) => {
    useAuthStore.setState({ user: session?.user ?? null, loading: false });
});
