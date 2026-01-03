import { makeAssistantToolUI } from "@assistant-ui/react";
import { Box, Save } from "lucide-react";
import { useState } from "react";

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

type BOMRow = {
  id: string;
  pos?: string | number;
  item_nr?: string;
  component: string; // fallback
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

const BOMTable = ({ args }: { args: BOMTableArgs }) => {
  const [data, setData] = useState(args.rows);
  const [isSaved, setIsSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Generic change handler
  const handleFieldChange = (index: number, field: keyof BOMRow, value: string | number) => {
    const updated = [...data];
    if (updated[index]) {
      // @ts-ignore - dynamic assignment
      updated[index][field] = value;
      setData(updated);
      setIsSaved(false);
    }
  };

  const handleSave = async () => {
    setSaveError(null);
    try {
      const payload = {
        user_query: "__BOM_CONFIRM__",
        thread_id: args.thread_id,
        bom_update: {
          bom_id: args.bom_id,
          overrides: data.map((row) => ({
            item_id: row.id,
            quantity: Number(row.quantity),
            item_nr: row.item_nr || null,
            description: row.description || row.component,
            unit: row.unit
          })),
        },
      };

      console.log("Saving BOM Update Payload:", payload); // <-- Check Console for this!

      const res = await fetch(`${BACKEND_BASE_URL}/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        setSaveError(await res.text());
        setIsSaved(false);
        return;
      }
      setIsSaved(true);
      console.log("Server responded: Success", await res.json());
    } catch (e) {
      console.error("Save failed", e);
      setSaveError(e instanceof Error ? e.message : "Unknown error");
      setIsSaved(false);
    }
  };

  return (
    <div className="border border-slate-800 rounded-xl overflow-hidden my-4 bg-slate-900 shadow-lg font-sans w-full">
      {/* HEADER */}
      <div className="bg-slate-950/50 px-4 py-3 font-semibold text-sm border-b border-slate-800 flex items-center justify-between text-slate-200">
        <div className="flex items-center gap-2">
          <Box size={16} className="text-indigo-400" />
          <span>Stückliste bearbeiten</span>
        </div>
        <span className="text-[10px] uppercase tracking-wider font-bold text-indigo-300 bg-indigo-500/10 px-2 py-1 rounded border border-indigo-500/20">
          Full Edit
        </span>
      </div>

      {/* TABELLE */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left whitespace-nowrap">
          <thead className="bg-slate-950/30 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-3 py-2 font-medium w-12">Pos.</th>
              <th className="px-3 py-2 font-medium w-24">Art.Nr.</th>
              <th className="px-3 py-2 font-medium">Beschreibung</th>
              <th className="px-3 py-2 font-medium w-20 text-right">Menge</th>
              <th className="px-3 py-2 font-medium w-16">Einh.</th>
            </tr>
          </thead>
          <tbody className="text-slate-300">
            {data.map((row, i) => (
              <tr
                key={i}
                className="border-b border-slate-800/50 last:border-0 hover:bg-slate-800/50 transition-colors"
              >
                {/* POS (Readonly) */}
                <td className="px-3 py-2 text-slate-500 font-mono text-xs">
                  {row.pos || i + 1}
                </td>

                {/* ART.NR */}
                <td className="px-3 py-2">
                  <input
                    value={row.item_nr || ""}
                    onChange={(e) => handleFieldChange(i, "item_nr", e.target.value)}
                    className="w-full bg-transparent border-none text-slate-300 focus:ring-0 focus:text-indigo-200 placeholder:text-slate-700"
                    placeholder="-"
                  />
                </td>

                {/* BESCHREIBUNG */}
                <td className="px-3 py-2">
                  <input
                    value={row.description || row.component}
                    onChange={(e) => handleFieldChange(i, "description", e.target.value)}
                    className="w-full bg-transparent border-none text-slate-200 font-medium focus:ring-0 focus:text-white"
                  />
                </td>

                {/* MENGE */}
                <td className="px-3 py-2 text-right">
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={row.quantity}
                    onChange={(e) => handleFieldChange(i, "quantity", e.target.value)}
                    className="w-16 text-right bg-slate-950/50 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 focus:ring-1 focus:ring-indigo-500 outline-none"
                  />
                </td>

                {/* EINHEIT */}
                <td className="px-3 py-2">
                  <input
                    value={row.unit}
                    onChange={(e) => handleFieldChange(i, "unit", e.target.value)}
                    className="w-12 bg-transparent border-none text-slate-400 text-xs focus:ring-0 focus:text-indigo-300 text-center"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* FOOTER */}
      <div className="p-3 bg-slate-950/30 border-t border-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {data.length} Positionen
        </span>

        <button
          onClick={handleSave}
          className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all shadow-lg ${isSaved
            ? "bg-green-500/10 text-green-400 border border-green-500/20"
            : "bg-indigo-600 text-white hover:bg-indigo-500 shadow-indigo-900/20"
            }`}
        >
          {isSaved ? "Gespeichert!" : "Änderungen übernehmen"}
          {!isSaved && <Save size={12} />}
        </button>
      </div>

      {saveError && (
        <div className="px-4 py-2 text-xs text-red-700 bg-red-50 border-t border-red-500/20">
          Fehler: {saveError}
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
