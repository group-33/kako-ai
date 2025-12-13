import { makeAssistantToolUI } from "@assistant-ui/react";
import { ShoppingCart, Package } from "lucide-react";

type SupplierOption = {
    supplier: string;
    part_number: string;
    price_per_unit: number;
    currency: string;
    min_order_quantity: number;
    delivery_time_days: number;
    in_stock: boolean;
    link: string;
};

type ProcurementItem = {
    component_name: string;
    options: SupplierOption[];
};

type ProcurementData = {
    items_to_procure: ProcurementItem[];
};

const ProcurementTable = ({ data }: { data: ProcurementData }) => {
    return (
        <div className="flex flex-col gap-4 my-4 w-full">
            {data.items_to_procure.map((item, idx) => (
                <div
                    key={idx}
                    className="border rounded-xl overflow-hidden bg-white shadow-sm font-sans"
                >
                    {/* Header */}
                    <div className="bg-slate-50 px-4 py-3 border-b flex items-center gap-2">
                        <Package size={16} className="text-purple-600" />
                        <h3 className="font-semibold text-slate-800 text-sm">
                            Beschaffung für: <span className="text-purple-700">{item.component_name}</span>
                        </h3>
                    </div>

                    {/* Options Grid */}
                    <div className="divide-y">
                        {item.options.map((option, optIdx) => (
                            <div
                                key={optIdx}
                                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50 transition-colors"
                            >
                                {/* Supplier Info */}
                                <div className="flex flex-col gap-1">
                                    <div className="font-bold text-slate-900 text-sm flex items-center gap-2">
                                        {option.supplier}
                                        {option.in_stock ? (
                                            <span className="bg-green-100 text-green-700 text-[10px] px-1.5 py-0.5 rounded-full font-medium">
                                                Auf Lager
                                            </span>
                                        ) : (
                                            <span className="bg-red-100 text-red-700 text-[10px] px-1.5 py-0.5 rounded-full font-medium">
                                                Nicht verfügbar
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                        Art.-Nr: {option.part_number}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                        Lieferzeit: {option.delivery_time_days} {option.delivery_time_days === 1 ? 'Tag' : 'Tage'}
                                    </div>
                                </div>

                                {/* Price & Action */}
                                <div className="flex items-center gap-4 sm:justify-end">
                                    <div className="text-right">
                                        <div className="font-bold text-slate-900 text-sm">
                                            {(option.price_per_unit).toLocaleString('de-DE', { style: 'currency', currency: option.currency })}
                                        </div>
                                        <div className="text-[10px] text-slate-400">
                                            pro Stk. (ab {option.min_order_quantity})
                                        </div>
                                    </div>

                                    <a
                                        href={option.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium px-3 py-2 rounded-lg transition-all"
                                    >
                                        <ShoppingCart size={14} />
                                        <span>Kaufen</span>
                                    </a>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

export const ProcurementOptionsTool = makeAssistantToolUI({
    toolName: "display_procurement_options",
    render: ({ args }) => {
        return <ProcurementTable data={args as ProcurementData} />;
    },
});
