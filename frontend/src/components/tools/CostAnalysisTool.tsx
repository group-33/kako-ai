import { makeAssistantToolUI } from "@assistant-ui/react";
import type { TooltipContentProps } from "recharts";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Euro, TrendingUp } from "lucide-react";
import { useTranslation } from "react-i18next";

type CostItem = {
    category: string;
    amount: number;
    color?: string;
};

type CostAnalysisData = {
    total_cost: number;
    items: CostItem[];
};

const CustomTooltip = ({
    active,
    payload,
    label,
    formatter,
}: Partial<TooltipContentProps<number, string>> & { formatter: Intl.NumberFormat }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border rounded-lg shadow-lg text-xs font-sans">
                <p className="font-semibold text-slate-800 mb-1">{label}</p>
                <p className="text-purple-600 font-bold">
                    {formatter.format(Number(payload[0]?.value ?? 0))}
                </p>
            </div>
        );
    }
    return null;
};

const CostAnalysisChart = ({ data }: { data: CostAnalysisData }) => {
    const { t, i18n } = useTranslation();
    const formatter = new Intl.NumberFormat(i18n.language, {
        style: "currency",
        currency: "EUR",
    });
    return (
        <div className="border rounded-xl overflow-hidden bg-white shadow-sm font-sans w-full my-4">
            <div className="bg-slate-50 px-4 py-3 border-b flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <TrendingUp size={16} className="text-purple-600" />
                    <h3 className="font-semibold text-slate-800 text-sm">
                        {t("costAnalysis.title")}
                    </h3>
                </div>
                <div className="flex items-center gap-1 text-slate-700 font-bold text-sm bg-purple-50 px-2 py-1 rounded border border-purple-100">
                    <Euro size={12} />
                    {formatter.format(data.total_cost)}
                </div>
            </div>

            <div className="p-4 w-full" style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.items} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis
                            dataKey="category"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 10, fill: "#64748b" }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 10, fill: "#64748b" }}
                            tickFormatter={(value) => formatter.format(Number(value))}
                        />
                        <Tooltip content={<CustomTooltip formatter={formatter} />} cursor={{ fill: "#f8fafc" }} />
                        <Bar dataKey="amount" radius={[4, 4, 0, 0]} maxBarSize={50}>
                            {data.items.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color || "#9333ea"} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div className="px-4 py-3 bg-slate-50 border-t text-xs text-slate-500">
                {t("costAnalysis.footer")}
            </div>
        </div>
    );
};

export const CostAnalysisTool = makeAssistantToolUI({
    toolName: "display_cost_analysis",
    render: ({ args }) => {
        return <CostAnalysisChart data={args as CostAnalysisData} />;
    },
});
