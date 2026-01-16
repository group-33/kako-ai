import { create } from "zustand";
import { persist } from "zustand/middleware";

export type User = {
    name: string;
    email: string;
};

type AuthStore = {
    isAuthenticated: boolean;
    user: User | null;
    login: (name: string, email: string) => void;
    logout: () => void;
    updateProfile: (name: string, email: string) => void;
};

export const useAuthStore = create<AuthStore>()(
    persist(
        (set) => ({
            isAuthenticated: false,
            user: null,

            login: (name, email) => {
                set({
                    isAuthenticated: true,
                    user: { name, email },
                });
            },

            logout: () => {
                set({
                    isAuthenticated: false,
                    user: null,
                });
            },

            updateProfile: (name, email) => {
                set((state) => ({
                    user: state.user ? { ...state.user, name, email } : null,
                }));
            },
        }),
        {
            name: "kako-auth-storage",
        }
    )
);
