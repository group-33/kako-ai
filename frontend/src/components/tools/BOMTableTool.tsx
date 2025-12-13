import { makeAssistantToolUI } from "@assistant-ui/react";
import { Box, Save } from "lucide-react";
import { useState } from "react";

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

type BOMRow = { id: string; component: string; quantity: number; unit: string };
type BOMTableArgs = {
  bom_id: string;
  thread_id: string;
  source_document?: string;
  rows: BOMRow[];
};

const BOMTable = ({ args }: { args: BOMTableArgs }) => {
  // Lokaler State macht die Tabelle editierbar!
  const [data, setData] = useState(args.rows);
  const [isSaved, setIsSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Funktion zum Ändern der Menge
  const handleQuantityChange = (index: number, newVal: string) => {
    const updated = [...data];
    if (updated[index]) {
      updated[index].quantity = Number(newVal);
      setData(updated);
      setIsSaved(false); // Wenn man tippt, ist es noch nicht gespeichert
    }
  };

  const handleSave = async () => {
    setSaveError(null);
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: "__BOM_CONFIRM__",
          thread_id: args.thread_id,
          bom_update: {
            bom_id: args.bom_id,
            overrides: data.map((row) => ({
              item_id: row.id,
              quantity: row.quantity,
            })),
          },
        }),
      });

      if (!res.ok) {
        setSaveError(await res.text());
        setIsSaved(false);
        return;
      }
      setIsSaved(true);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Unknown error");
      setIsSaved(false);
    }
  };

  return (
    <div className="border rounded-xl overflow-hidden my-4 bg-white shadow-sm font-sans w-full">
      {/* HEADER */}
      <div className="bg-slate-50 px-4 py-3 font-semibold text-sm border-b flex items-center justify-between text-slate-800">
        <div className="flex items-center gap-2">
          <Box size={16} className="text-blue-600" />
          <span>Stückliste bearbeiten</span>
        </div>
        <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500 bg-slate-200/50 px-2 py-1 rounded">
          Edit Mode
        </span>
      </div>

      {/* TABELLE */}
      <table className="w-full text-sm text-left">
        <thead className="bg-white text-slate-400 border-b">
          <tr>
            <th className="px-4 py-2 font-medium">Komponente</th>
            {/* Status Spalte entfernt, Menge verbreitert */}
            <th className="px-4 py-2 font-medium w-32 text-right">Menge</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className="border-b last:border-0 hover:bg-slate-50 transition-colors"
            >
              <td className="px-4 py-3 font-medium text-slate-700 align-middle">
                {row.component}
              </td>
              <td className="px-4 py-2 align-middle text-right">
                <div className="flex items-center justify-end gap-2">
                  {/* EDITIERBARES FELD */}
                  <input
                    type="number"
                    min="0"
                    value={row.quantity}
                    onChange={(e) => handleQuantityChange(i, e.target.value)}
                    className="w-16 px-2 py-1 text-right border rounded bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                  <span className="text-slate-400 text-xs w-6 text-left">
                    {row.unit}
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* FOOTER MIT AKTION */}
      <div className="p-3 bg-slate-50 border-t flex items-center justify-between">
        <span className="text-xs text-slate-400">
          Automatisch aus Zeichnung{" "}
          {args.source_document ? `"${args.source_document}"` : "extrahiert"}
        </span>

        <button
          onClick={handleSave}
          className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all ${isSaved
              ? "bg-green-100 text-green-700 border border-green-200"
              : "bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
            }`}
        >
          {isSaved ? "Gespeichert!" : "Bestätigen"}
          {!isSaved && <Save size={12} />}
        </button>
      </div>

      {saveError && (
        <div className="px-4 py-2 text-xs text-red-700 bg-red-50 border-t">
          Speichern fehlgeschlagen: {saveError}
        </div>
      )}
    </div>
  );
};

export const BOMTableTool = makeAssistantToolUI({
  toolName: "display_bom_table",
  render: ({ args }) => {
    return <BOMTable args={args as unknown as BOMTableArgs} />;
  },
});
