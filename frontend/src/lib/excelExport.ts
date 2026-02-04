import * as XLSX from 'xlsx';
import { useChatStore } from '@/store/useChatStore';

type BOMRow = {
    id: string;
    pos?: string | number;
    item_nr?: string;
    component: string;
    description?: string;
    quantity: number;
    unit: string;
};

type BOMTableArgs = {
    bom_id: string;
    thread_id: string;
    source_document?: string;
    rows: BOMRow[];
};

type ToolCallPart = {
    type: "tool-call";
    toolName: string;
    args?: unknown;
};

const isToolCallPart = (part: unknown): part is ToolCallPart => {
    return (
        typeof part === "object" &&
        part !== null &&
        "type" in part &&
        "toolName" in part &&
        (part as ToolCallPart).type === "tool-call"
    );
};

const isBOMTableArgs = (value: unknown): value is BOMTableArgs => {
    return (
        typeof value === "object" &&
        value !== null &&
        "bom_id" in value &&
        "thread_id" in value &&
        "rows" in value
    );
};

export const exportBOMsFromMessage = (threadId: string, currentBomId: string) => {
    const { threads } = useChatStore.getState();
    const thread = threads.find(t => t.id === threadId);
    if (!thread || !thread.messages) {
        console.error("Thread or messages not found");
        return;
    }

    // Find the message that contains this BOM
    const targetMessage = thread.messages.find((message) => {
        const content = message.content;
        if (!Array.isArray(content)) return false;
        return content.some((part) => {
            if (!isToolCallPart(part)) return false;
            if (part.toolName !== "display_bom_table") return false;
            if (!isBOMTableArgs(part.args)) return false;
            return part.args.bom_id === currentBomId;
        });
    });

    if (!targetMessage) {
        console.error("Message containing BOM not found");
        return;
    }

    // Extract ALL BOMs from this message
    if (!Array.isArray(targetMessage.content)) return;

    const boms = targetMessage.content
        .filter(isToolCallPart)
        .filter((part) => part.toolName === "display_bom_table" && isBOMTableArgs(part.args))
        .map((part) => part.args) as BOMTableArgs[];

    if (boms.length === 0) return;

    // Create Workbook
    const wb = XLSX.utils.book_new();

    boms.forEach((bomArgs: BOMTableArgs, index: number) => {
        // Determine Sheet Name (max 31 chars)
        let sheetName = bomArgs.source_document
            ? bomArgs.source_document.split('/').pop()?.slice(0, 30)
            : `BOM ${index + 1}`;

        // Ensure unique sheet names
        if (wb.SheetNames.includes(sheetName || "")) {
            sheetName = `${sheetName} (${index})`;
        }

        // Format Data for Excel
        const wsData = bomArgs.rows.map((row: BOMRow) => ({
            Position: row.pos,
            'Art.Nr.': row.item_nr,
            Beschreibung: row.description || row.component,
            Menge: row.quantity,
            Einheit: row.unit
        }));

        const ws = XLSX.utils.json_to_sheet(wsData);

        // Set column widths
        ws['!cols'] = [
            { wch: 8 },  // Pos
            { wch: 15 }, // Art.Nr
            { wch: 40 }, // Desc
            { wch: 10 }, // Qty
            { wch: 10 }  // Unit
        ];

        XLSX.utils.book_append_sheet(wb, ws, sheetName);
    });

    // Download File
    const filename = `KakoAI_Export_${new Date().toISOString().slice(0, 10)}.xlsx`;
    XLSX.writeFile(wb, filename);
};
