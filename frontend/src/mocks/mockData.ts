export const BOM_DATA = {
    rows: [
        { component: "Gehäuseoberschale (ALU)", quantity: 1, unit: "Stk" },
        { component: "Platine Mainboard v2.4", quantity: 1, unit: "Stk" },
        { component: "Schrauben M4x10", quantity: 12, unit: "Stk" },
        { component: "Wärmeleitpaste", quantity: 2, unit: "g" },
        { component: "Verbindungskabel Molex", quantity: 3, unit: "Stk" },
    ],
};

export const PROCUREMENT_DATA = {
    items_to_procure: [
        {
            component_name: "Schrauben M4x10",
            options: [
                {
                    supplier: "Würth",
                    part_number: "ISO-4762-M4x10",
                    price_per_unit: 0.12,
                    currency: "EUR",
                    min_order_quantity: 100,
                    delivery_time_days: 2,
                    in_stock: true,
                    link: "https://eshop.wuerth.de",
                },
                {
                    supplier: "Schrauben24",
                    part_number: "S-M4-10-VA",
                    price_per_unit: 0.09,
                    currency: "EUR",
                    min_order_quantity: 500,
                    delivery_time_days: 5,
                    in_stock: true,
                    link: "https://example.com/screws",
                },
            ],
        },
        {
            component_name: "Wärmeleitpaste",
            options: [
                {
                    supplier: "Conrad",
                    part_number: "MX-4-2019",
                    price_per_unit: 8.99,
                    currency: "EUR",
                    min_order_quantity: 1,
                    delivery_time_days: 1,
                    in_stock: true,
                    link: "https://conrad.de",
                },
            ],
        },
    ],
};

export const COST_ANALYSIS_DATA = {
    total_cost: 365.12,
    items: [
        { category: "Elektronik", amount: 180.50, color: "#9333ea" }, // Purple
        { category: "Mechanik", amount: 120.00, color: "#2563eb" }, // Blue
        { category: "Verbindung", amount: 45.12, color: "#0891b2" }, // Cyan
        { category: "Sonstiges", amount: 19.50, color: "#cbd5e1" }, // Slate
    ],
};
