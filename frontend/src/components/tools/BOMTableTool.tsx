import { makeAssistantToolUI } from "@assistant-ui/react";
import { Box, Save, ChevronDown, ChevronRight, Download, Trash2, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { exportBOMsFromMessage } from "@/lib/excelExport";
import { useTranslation } from "react-i18next";
import { useMetricsStore } from "@/store/useMetricsStore";
import { supabase } from "@/lib/supabase";

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

type BOMRow = {
  id: string;
  pos?: string | number;
  item_nr?: string;
  xentral_number?: string;
  component: string; // fallback
  description?: string;
  quantity: number;
  unit: string;
};

type BOMTableArgs = {
  bom_id: string;
  thread_id: string;
  source_document?: string;
  preview_image?: string;
  title?: string;
  orientation?: "portrait" | "landscape";
  rows: BOMRow[];
};

const BOMTable = ({ args }: { args: BOMTableArgs }) => {
  const { t } = useTranslation();
  const registerBom = useMetricsStore(s => s.registerBom);
  const updateBomEdits = useMetricsStore(s => s.updateBomEdits);
  const [data, setData] = useState(args.rows);
  const [isSaved, setIsSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(true);
  // Add local state for title
  const [title, setTitle] = useState(args.title || "");
  const initialRowsRef = useRef<BOMRow[]>(args.rows);

  useEffect(() => {
    const clonedRows = args.rows.map(row => ({ ...row }));
    initialRowsRef.current = clonedRows.map(row => ({ ...row }));
    setData(clonedRows);
    setTitle(args.title || "");
  }, [args.bom_id, args.rows, args.title]);

  useEffect(() => {
    registerBom(args.bom_id, args.rows.length);
  }, [args.bom_id, args.rows.length, registerBom]);

  const computeChangedRows = (initialRows: BOMRow[], currentRows: BOMRow[]) => {
    const normalize = (row: BOMRow) => ({
      item_nr: row.item_nr ?? "",
      xentral_number: row.xentral_number ?? "",
      description: (row.description ?? row.component ?? "").trim(),
      quantity: Number(row.quantity) || 0,
      unit: (row.unit ?? "").trim(),
    });

    const initialMap = new Map(initialRows.map(row => [row.id, normalize(row)]));
    const currentMap = new Map(currentRows.map(row => [row.id, normalize(row)]));

    let changed = 0;
    for (const [id, current] of currentMap.entries()) {
      const initial = initialMap.get(id);
      if (!initial) {
        changed += 1;
        continue;
      }
      if (
        current.item_nr !== initial.item_nr ||
        current.xentral_number !== initial.xentral_number ||
        current.description !== initial.description ||
        current.quantity !== initial.quantity ||
        current.unit !== initial.unit
      ) {
        changed += 1;
      }
    }

    for (const id of initialMap.keys()) {
      if (!currentMap.has(id)) {
        changed += 1;
      }
    }

    const total = Math.max(initialRows.length, currentRows.length);
    return { changed, total };
  };

  const handleFieldChange = (index: number, field: keyof BOMRow, value: string | number) => {
    setData(prev => {
      if (!prev[index]) return prev;
      const updated = prev.map((row, i) =>
        i === index ? { ...row, [field]: value } : row
      );
      return updated;
    });
    setIsSaved(false);
  };

  const handleAddRow = () => {
    const newRow: BOMRow = {
      id: `new_${Date.now()}`,
      pos: data.length + 1,
      item_nr: "",
      xentral_number: "",
      component: "", // description will be used
      description: "",
      quantity: 1,
      unit: "Stk",
    };
    setData(prev => [...prev, newRow]);
    setIsSaved(false);
  };

  const handleDeleteRow = (index: number) => {
    setData(prev => prev.filter((_, i) => i !== index));
    setIsSaved(false);
  };

  const handleSave = async () => {
    setSaveError(null);
    setIsSaving(true);
    try {
      const payload = {
        user_query: "__BOM_CONFIRM__",
        thread_id: args.thread_id,
        bom_update: {
          bom_id: args.bom_id,
          title: title, // Send updated title
          overrides: data.map((row) => ({
            item_id: row.id,
            quantity: Number(row.quantity),
            item_nr: row.item_nr || null,
            xentral_number: row.xentral_number || null,
            description: row.description || row.component,
            unit: row.unit
          })),
        },
      };

      console.log("Saving BOM Update Payload:", payload);

      // Get current session token
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) {
        throw new Error("Not authenticated");
      }

      const res = await fetch(`${BACKEND_BASE_URL}/agent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        setSaveError(await res.text());
        setIsSaved(false);
        setIsSaving(false);
        return;
      }
      setIsSaved(true);
      const { changed, total } = computeChangedRows(initialRowsRef.current, data);
      updateBomEdits(args.bom_id, changed, total || 0);
      console.log("Server responded: Success", await res.json());
    } catch (e) {
      console.error("Save failed", e);
      setSaveError(e instanceof Error ? e.message : "Unknown error");
      setIsSaved(false);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="border border-slate-800 rounded-xl overflow-hidden my-4 bg-slate-900 shadow-lg font-sans w-full transition-all duration-300">
      <div
        className="w-full bg-slate-950/50 px-4 py-3 font-semibold text-sm border-b border-slate-800 flex items-center justify-between text-slate-200 transition-colors"
      >
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 hover:text-white transition-colors focus:outline-none"
        >
          {isOpen ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
          <Box size={16} className="text-sky-500" />
          {/* Editable Title Input */}
          <input
            value={title}
            onChange={(e) => {
              e.stopPropagation();
              setTitle(e.target.value);
            }}
            onClick={(e) => e.stopPropagation()} // Prevent toggle when clicking input
            className="bg-transparent border-none text-slate-200 font-semibold focus:ring-0 placeholder:text-slate-600 min-w-[200px]"
            placeholder={t("bomTable.title")}
          />
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={(e) => {
              e.stopPropagation(); // prevent toggle
              handleAddRow();
            }}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-sky-400 transition-colors px-2 py-1 hover:bg-slate-800/50 rounded"
            title={t("bomTable.addRowTitle")}
          >
            <Plus size={14} />
            <span>{t("bomTable.addRow")}</span>
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              exportBOMsFromMessage(args.thread_id, args.bom_id);
            }}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-green-400 transition-colors px-2 py-1 hover:bg-slate-800/50 rounded"
            title={t("bomTable.exportTitle")}
          >
            <Download size={14} />
            <span>{t("bomTable.export")}</span>
          </button>


        </div>
      </div>

      {isOpen && (
        <div className="animate-in slide-in-from-top-2 duration-200 flex flex-col border-t border-slate-800">

          <div className="flex-1 min-w-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left whitespace-nowrap">
                <thead className="bg-slate-950/30 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2 font-medium w-12">{t("bomTable.headers.position")}</th>
                    <th className="px-3 py-2 font-medium w-24">{t("bomTable.headers.itemNumber")}</th>
                    <th className="px-3 py-2 font-medium w-32">{t("bomTable.headers.xentral_number")}</th>
                    <th className="px-3 py-2 font-medium">{t("bomTable.headers.description")}</th>
                    <th className="px-3 py-2 font-medium w-20 text-right">{t("bomTable.headers.quantity")}</th>
                    <th className="px-3 py-2 font-medium w-16">{t("bomTable.headers.unit")}</th>
                    <th className="px-1 py-2 w-8"></th>
                  </tr>
                </thead>
                <tbody className="text-slate-300">
                  {data.map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-slate-800/50 last:border-0 hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="px-3 py-2 text-slate-500 font-mono text-xs">
                        {row.pos || i + 1}
                      </td>

                      <td className="px-3 py-2">
                        <input
                          value={row.item_nr || ""}
                          onChange={(e) => handleFieldChange(i, "item_nr", e.target.value)}
                          className="w-full bg-transparent border-none text-slate-300 focus:ring-0 focus:text-sky-200 placeholder:text-slate-700"
                          placeholder="-"
                        />
                      </td>

                      <td className="px-3 py-2">
                        <input
                          value={row.xentral_number || ""}
                          onChange={(e) => handleFieldChange(i, "xentral_number", e.target.value)}
                          className="w-full bg-transparent border-none text-slate-300 focus:ring-0 focus:text-sky-200 placeholder:text-slate-700"
                          placeholder="Not Matched"
                        />
                      </td>

                      <td className="px-3 py-2">
                        <input
                          value={row.description || row.component}
                          onChange={(e) => handleFieldChange(i, "description", e.target.value)}
                          className="w-full bg-transparent border-none text-slate-200 font-medium focus:ring-0 focus:text-white"
                        />
                      </td>

                      <td className="px-3 py-2 text-right">
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={row.quantity}
                          onChange={(e) => handleFieldChange(i, "quantity", e.target.value)}
                          className="bom-qty-input w-16 text-right bg-slate-950/50 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 focus:ring-1 focus:ring-sky-500 outline-none"
                        />
                      </td>

                      <td className="px-3 py-2">
                        <input
                          value={row.unit}
                          onChange={(e) => handleFieldChange(i, "unit", e.target.value)}
                          className="w-12 bg-transparent border-none text-slate-400 text-xs focus:ring-0 focus:text-sky-300 text-center"
                        />
                      </td>
                      <td className="px-1 py-1 text-center">
                        <button
                          onClick={() => handleDeleteRow(i)}
                          className="p-1 text-slate-600 hover:text-red-400 hover:bg-red-900/20 rounded transition-colors"
                          title={t("bomTable.deleteRowTitle")}
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-950/30 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {t("bomTable.positions", { count: data.length })}
              </span>

              <button
                onClick={handleSave}
                disabled={isSaving}
                className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all shadow-lg ${isSaved
                  ? "bg-green-500/10 text-green-400 border border-green-500/20"
                  : "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-900/20 disabled:opacity-50 disabled:cursor-wait"
                  }`}
              >
                {isSaving
                  ? t("bomTable.save.saving")
                  : isSaved
                    ? t("bomTable.save.saved")
                    : t("bomTable.save.apply")}
                {!isSaved && !isSaving && <Save size={12} />}
                {isSaving && <div className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
              </button>
            </div>

            {saveError && (
              <div className="px-4 py-2 text-xs text-red-700 bg-red-50 border-t border-red-500/20">
                {t("bomTable.save.error")}: {saveError}
              </div>
            )}
          </div>

          {(args.preview_image || args.source_document) && (
            <div className="w-full border-t border-slate-800 bg-slate-950/20 p-4 flex flex-col gap-2">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                {t("bomTable.sourceFile")}
              </span>
              <div className="relative group rounded overflow-hidden border border-slate-800 bg-slate-950 shadow-inner">
                {(() => {
                  const rawSrc = args.preview_image || args.source_document || "";
                  const imgSrc = rawSrc.startsWith('/') ? `${BACKEND_BASE_URL}${rawSrc}` : rawSrc;

                  if (imgSrc.toLowerCase().endsWith(".pdf")) {
                    return (
                      <iframe
                        src={`${imgSrc}#view=Fit`}
                        className={`w-full border border-slate-800 rounded bg-slate-950 ${args.orientation === "landscape" ? "aspect-[29/23]" : "aspect-[21/31]"}`}
                        title={t("bomTable.sourceAlt")}
                      />
                    );
                  }

                  return (
                    <img
                      src={imgSrc}
                      alt={t("bomTable.sourceAlt")}
                      className="w-full h-auto object-contain"
                    />
                  );
                })()}
              </div>
            </div>
          )}
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
