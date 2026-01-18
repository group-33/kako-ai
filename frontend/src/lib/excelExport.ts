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

export const exportBOMsFromMessage = (threadId: string, currentBomId: string) => {
    const { threads } = useChatStore.getState();
    const thread = threads.find(t => t.id === threadId);
    if (!thread || !thread.messages) {
        console.error("Thread or messages not found");
        return;
    }

    // Find the message that contains this BOM
    const targetMessage = thread.messages.find(m => {
        if (typeof m.content !== 'object' || !Array.isArray(m.content)) return false;
        return m.content.some((block: any) =>
            block.type === 'tool-call' &&
            block.toolName === 'display_bom_table' &&
            block.args?.bom_id === currentBomId
        );
    });

    if (!targetMessage) {
        console.error("Message containing BOM not found");
        return;
    }

    // Extract ALL BOMs from this message
    if (!Array.isArray(targetMessage.content)) return;

    const boms = targetMessage.content
        .filter((block: any) => block.type === 'tool-call' && block.toolName === 'display_bom_table')
        .map((block: any) => block.args as BOMTableArgs);

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
    const filename = `KAkoAI_Export_${new Date().toISOString().slice(0, 10)}.xlsx`;
    XLSX.writeFile(wb, filename);
};
