import { makeAssistantToolUI } from "@assistant-ui/react";
import { ShoppingCart, Package, Check, Trophy, Timer } from "lucide-react";
import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";

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

type SortKey = "price" | "delivery";

const ProcurementTable = ({ data }: { data: ProcurementData }) => {
    return (
        <div className="flex flex-col gap-6 my-4 w-full">
            {data.items_to_procure.map((item, idx) => (
                <ItemCard key={idx} item={item} />
            ))}
        </div>
    );
};

const ItemCard = ({ item }: { item: ProcurementItem }) => {
    const [sortBy, setSortBy] = useState<SortKey>("price");
    const [selectedKey, setSelectedKey] = useState<string | null>(null);

    // Find best values for badges
    const bestPrice = item.options.length
        ? Math.min(...item.options.map((o) => o.price_per_unit))
        : 0;
    const bestDelivery = item.options.length
        ? Math.min(...item.options.map((o) => o.delivery_time_days))
        : 0;

    // Sort options
    const sortedOptions = useMemo(() => {
        return [...item.options].sort((a, b) => {
            if (sortBy === "price") {
                return a.price_per_unit - b.price_per_unit;
            } else {
                return a.delivery_time_days - b.delivery_time_days;
            }
        });
    }, [item.options, sortBy]);

    const selectedOption =
        selectedKey !== null
            ? item.options.find((option) =>
                  buildOptionKey(option) === selectedKey,
              )
            : undefined;

    if (!item.options.length) {
        return (
            <div className="border rounded-xl overflow-hidden bg-white shadow-sm font-sans ring-1 ring-slate-200">
                <div className="bg-slate-50 px-4 py-3 border-b flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Package size={18} className="text-purple-600" />
                        <h3 className="font-semibold text-slate-800 text-sm">
                            {item.component_name}
                        </h3>
                    </div>
                </div>
                <div className="p-4 text-sm text-slate-500">
                    No supplier options available.
                </div>
            </div>
        );
    }

    return (
        <div className="border rounded-xl overflow-hidden bg-white shadow-sm font-sans ring-1 ring-slate-200">
            {/* Header */}
            <div className="bg-slate-50 px-4 py-3 border-b flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Package size={18} className="text-purple-600" />
                    <h3 className="font-semibold text-slate-800 text-sm">
                        {item.component_name}
                    </h3>
                </div>

                {/* Sort Controls */}
                <div className="flex bg-white rounded-lg p-1 border shadow-sm">
                    <button
                        onClick={() => setSortBy("price")}
                        className={cn(
                            "px-2 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1",
                            sortBy === "price" ? "bg-purple-100 text-purple-700" : "text-slate-500 hover:bg-slate-50"
                        )}
                    >
                        Preis
                    </button>
                    <button
                        onClick={() => setSortBy("delivery")}
                        className={cn(
                            "px-2 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1",
                            sortBy === "delivery" ? "bg-purple-100 text-purple-700" : "text-slate-500 hover:bg-slate-50"
                        )}
                    >
                        Lieferzeit
                    </button>
                </div>
            </div>

            {/* Options Grid */}
            <div className="divide-y relative">
                {sortedOptions.map((option, idx) => {
                    const optionKey = buildOptionKey(option);
                    // Determine badges
                    const isBestPrice = option.price_per_unit === bestPrice;
                    const isFastest = option.delivery_time_days === bestDelivery;
                    const isSelected = selectedKey === optionKey;

                    return (
                        <div
                            key={idx}
                            onClick={() => setSelectedKey(optionKey)}
                            className={cn(
                                "p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer transition-all border-l-4",
                                isSelected
                                    ? "bg-purple-50/50 border-l-purple-600"
                                    : "border-l-transparent hover:bg-slate-50"
                            )}
                        >
                            {/* Left Section: Supplier & Badges */}
                            <div className="flex flex-col gap-1.5 flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="font-bold text-slate-900 text-sm">{option.supplier}</span>
                                    {option.in_stock ? (
                                        <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-medium">Available</span>
                                    ) : (
                                        <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">Out of stock</span>
                                    )}

                                    {isBestPrice && (
                                        <span className="flex items-center gap-1 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded font-medium ring-1 ring-yellow-200">
                                            <Trophy size={10} /> Best Price
                                        </span>
                                    )}

                                    {isFastest && (
                                        <span className="flex items-center gap-1 text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded font-medium ring-1 ring-blue-200">
                                            <Timer size={10} /> Fastest
                                        </span>
                                    )}
                                </div>

                                <div className="flex flex-col gap-0.5 text-xs text-slate-500">
                                    <span>Part: {option.part_number}</span>
                                    <span>Delivery: <strong className="text-slate-700">{option.delivery_time_days} days</strong></span>
                                </div>
                            </div>

                            {/* Right Section: Price & CTA */}
                            <div className="flex items-center justify-between sm:justify-end gap-6 min-w-[140px]">
                                <div className="text-right">
                                    <div className="font-bold text-slate-900 text-base">
                                        {(option.price_per_unit).toLocaleString('de-DE', { style: 'currency', currency: option.currency })}
                                    </div>
                                    <div className="text-[10px] text-slate-400">
                                        per unit (min. {option.min_order_quantity})
                                    </div>
                                </div>

                                <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center transition-all",
                                    isSelected ? "bg-purple-600 text-white shadow-md scale-110" : "bg-slate-100 text-slate-300"
                                )}>
                                    {isSelected ? <Check size={16} /> : <div className="w-2 h-2 rounded-full bg-slate-300" />}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Footer / Selection Action */}
            {selectedOption && (
                <div className="bg-purple-50 px-4 py-2 border-t border-purple-100 flex justify-between items-center animate-in slide-in-from-bottom-2 fade-in">
                    <span className="text-xs text-purple-800 font-medium">
                        Selected: {selectedOption.supplier}
                    </span>
                    <a
                        href={selectedOption.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-all shadow-sm"
                    >
                        <ShoppingCart size={14} />
                        Order
                    </a>
                </div>
            )}
        </div>
    );
};

export const ProcurementOptionsTool = makeAssistantToolUI({
    toolName: "display_procurement_options",
    render: ({ args }) => {
        return <ProcurementTable data={args as ProcurementData} />;
    },
});

const buildOptionKey = (option: SupplierOption) =>
    `${option.supplier}::${option.part_number}::${option.price_per_unit}`;
