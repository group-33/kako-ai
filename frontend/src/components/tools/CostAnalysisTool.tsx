import { makeAssistantToolUI } from "@assistant-ui/react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Euro, TrendingUp } from "lucide-react";

type CostItem = {
    category: string;
    amount: number;
    color?: string;
};

type CostAnalysisData = {
    total_cost: number;
    items: CostItem[];
};

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border rounded-lg shadow-lg text-xs font-sans">
                <p className="font-semibold text-slate-800 mb-1">{label}</p>
                <p className="text-purple-600 font-bold">
                    {Number(payload[0].value).toLocaleString("de-DE", {
                        style: "currency",
                        currency: "EUR",
                    })}
                </p>
            </div>
        );
    }
    return null;
};

const CostAnalysisChart = ({ data }: { data: CostAnalysisData }) => {
    return (
        <div className="border rounded-xl overflow-hidden bg-white shadow-sm font-sans w-full my-4">
            
            <div className="bg-slate-50 px-4 py-3 border-b flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <TrendingUp size={16} className="text-purple-600" />
                    <h3 className="font-semibold text-slate-800 text-sm">
                        Kostenanalyse
                    </h3>
                </div>
                <div className="flex items-center gap-1 text-slate-700 font-bold text-sm bg-purple-50 px-2 py-1 rounded border border-purple-100">
                    <Euro size={12} />
                    {data.total_cost.toLocaleString("de-DE", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                    })}
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
                            tickFormatter={(value) => `${value}€`}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc" }} />
                        <Bar dataKey="amount" radius={[4, 4, 0, 0]} maxBarSize={50}>
                            {data.items.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color || "#9333ea"} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            
            <div className="px-4 py-3 bg-slate-50 border-t text-xs text-slate-500">
                Die Analyse basiert auf den aktuell ausgewählten Lieferantenoptionen.
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
