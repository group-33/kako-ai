import { create } from "zustand";
import { persist } from "zustand/middleware";

type BomMetrics = {
  totalRows: number;
  editedRows: number;
};

type MetricsState = {
  bomIds: Record<string, true>;
  bomStats: Record<string, BomMetrics>;
  feasibilityChecks: number;
  feasibilityEventIds: Record<string, true>;
  feasibilityChecksByWeek: Record<string, number>;
  procurementSpendEur: number;
  procurementOrders: number;
  procurementOrdersByMonth: Record<string, number>;
  registerBom: (bomId: string, totalRows: number) => void;
  updateBomEdits: (bomId: string, editedRows: number, totalRows: number) => void;
  resetMetrics: () => void;
  addProcurementOrder: (amountEur: number) => void;
  registerFeasibilityCheck: (eventId: string) => void;
};

export const useMetricsStore = create<MetricsState>()(
  persist(
    (set, get) => ({
      bomIds: {},
      bomStats: {},
      feasibilityChecks: 0,
      feasibilityEventIds: {},
      feasibilityChecksByWeek: {},
      procurementSpendEur: 0,
      procurementOrders: 0,
      procurementOrdersByMonth: {},
      registerBom: (bomId, totalRows) => {
        if (!bomId) return;
        const { bomIds, bomStats } = get();
        if (bomIds[bomId]) {
          const existing = bomStats[bomId];
          if (existing && totalRows > existing.totalRows) {
            set({
              bomStats: {
                ...bomStats,
                [bomId]: { ...existing, totalRows },
              },
            });
          }
          return;
        }
        set({
          bomIds: { ...bomIds, [bomId]: true },
          bomStats: {
            ...bomStats,
            [bomId]: { totalRows, editedRows: 0 },
          },
        });
      },
      updateBomEdits: (bomId, editedRows, totalRows) => {
        if (!bomId) return;
        const { bomIds, bomStats } = get();
        set({
          bomIds: bomIds[bomId] ? bomIds : { ...bomIds, [bomId]: true },
          bomStats: {
            ...bomStats,
            [bomId]: {
              totalRows,
              editedRows,
            },
          },
        });
      },
      resetMetrics: () => {
        set({
          bomIds: {},
          bomStats: {},
          feasibilityChecks: 0,
          feasibilityEventIds: {},
          feasibilityChecksByWeek: {},
          procurementSpendEur: 0,
          procurementOrders: 0,
          procurementOrdersByMonth: {},
        });
      },
      addProcurementOrder: (amountEur) => {
        if (!Number.isFinite(amountEur) || amountEur <= 0) return;
        const now = new Date();
        const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
        set((state) => ({
          procurementSpendEur: state.procurementSpendEur + amountEur,
          procurementOrders: state.procurementOrders + 1,
          procurementOrdersByMonth: {
            ...state.procurementOrdersByMonth,
            [monthKey]: (state.procurementOrdersByMonth[monthKey] || 0) + 1,
          },
        }));
      },
      registerFeasibilityCheck: (eventId) => {
        if (!eventId) return;
        const { feasibilityEventIds } = get();
        if (feasibilityEventIds[eventId]) return;
        const now = new Date();
        const weekKey = getWeekKey(now);
        set((state) => ({
          feasibilityChecks: state.feasibilityChecks + 1,
          feasibilityEventIds: { ...state.feasibilityEventIds, [eventId]: true },
          feasibilityChecksByWeek: {
            ...state.feasibilityChecksByWeek,
            [weekKey]: (state.feasibilityChecksByWeek[weekKey] || 0) + 1,
          },
        }));
      },
    }),
    { name: "kakoai-metrics" },
  ),
);

const getWeekKey = (date: Date) => {
  const start = new Date(date);
  const day = start.getDay(); // 0 = Sunday
  const diff = day === 0 ? -6 : 1 - day;
  start.setDate(start.getDate() + diff);
  start.setHours(0, 0, 0, 0);
  const y = start.getFullYear();
  const m = String(start.getMonth() + 1).padStart(2, "0");
  const d = String(start.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};
