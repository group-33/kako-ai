import { makeAssistantToolUI } from "@assistant-ui/react";
import { Box, Save } from "lucide-react";
import { useState } from "react";

// Wir definieren den Typ für eine Zeile
type BOMRow = { component: string; quantity: number; unit: string };

const BOMTable = ({ initialData }: { initialData: BOMRow[] }) => {
  // Lokaler State macht die Tabelle editierbar!
  const [data, setData] = useState(initialData);
  const [isSaved, setIsSaved] = useState(false);

  // Funktion zum Ändern der Menge
  const handleQuantityChange = (index: number, newVal: string) => {
    const updated = [...data];
    if (updated[index]) {
      updated[index].quantity = Number(newVal);
      setData(updated);
      setIsSaved(false); // Wenn man tippt, ist es noch nicht gespeichert
    }
  };

  // Funktion zum Simulieren des Speicherns
  const handleSave = () => {
    setIsSaved(true);
    // Hier würde man später die Daten ans Backend zurückschicken
    console.log("Neue Stückliste gespeichert:", data);
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
          {/* Dein gewünschter Text */}
          Automatisch aus Zeichnung "Name Zeichnung" extrahiert
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
    </div>
  );
};

export const BOMTableTool = makeAssistantToolUI({
  toolName: "display_bom_table",
  render: ({ args }) => {
    return <BOMTable initialData={args.rows as BOMRow[]} />;
  },
});
