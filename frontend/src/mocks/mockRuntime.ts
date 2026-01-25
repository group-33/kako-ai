import { useLocalRuntime } from "@assistant-ui/react";
import { BOM_DATA, PROCUREMENT_DATA, COST_ANALYSIS_DATA } from "./mockData";

export const useMockRuntime = () => {
    return useLocalRuntime({
        run: async function* ({ messages, abortSignal }) {
            const lastMessage = messages[messages.length - 1];
            if (!lastMessage || lastMessage.content[0]?.type !== "text") return;
            const userText = lastMessage.content[0].text.toLowerCase();
            await new Promise((resolve) => setTimeout(resolve, 600));
            if (abortSignal.aborted) return;
            if (userText.includes("stückliste")) {
                const text =
                    "Verstanden. Ich habe die technischen Daten analysiert. Hier ist die vorläufige Stückliste sowie passende Beschaffungsoptionen für die kritischen Komponenten:";

                for (let i = 0; i < text.length; i += 5) {
                    yield { content: [{ type: "text", text: text.slice(0, i + 5) }] };
                    await new Promise((resolve) => setTimeout(resolve, 20));
                }

                await new Promise((resolve) => setTimeout(resolve, 300));
                const pathMatch = lastMessage.content[0].text.match(
                    /(?:\/[^\s]+)+\.(?:png|jpg|jpeg|pdf)/i,
                );
                const filenameForBackend = pathMatch?.[0];
                const BACKEND_BASE_URL = (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

                if (filenameForBackend) {
                    try {
                        const res = await fetch(`${BACKEND_BASE_URL}/bom`, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify({ filename: filenameForBackend }),
                        });

                        if (!abortSignal.aborted && res.ok) {
                            const data = (await res.json());
                            const bomBlock = data.blocks.find(
                                (b: any) =>
                                    b.type === "tool_use" &&
                                    b.tool_name === "display_bom_table",
                            );

                            if (bomBlock) {
                                const toolCallId = `call_bom_${Date.now()}`;
                                const rows = Array.isArray((bomBlock.data as any).rows)
                                    ? ((bomBlock.data as any).rows ?? [])
                                    : [];

                                const args = { data: rows };

                                yield {
                                    content: [
                                        {
                                            type: "tool-call",
                                            toolName: "display_bom_table",
                                            toolCallId,
                                            args,
                                            argsText: JSON.stringify(args),
                                        },
                                    ],
                                };
                                return;
                            }
                        }
                    } catch {
                    }
                }

                yield {
                    content: [
                        {
                            type: "tool-call",
                            toolName: "display_bom_table",
                            toolCallId: "call_bom_123",
                            args: BOM_DATA,
                            argsText: JSON.stringify(BOM_DATA),
                        },
                        {
                            type: "tool-call",
                            toolName: "display_procurement_options",
                            toolCallId: "call_proc_456",
                            args: PROCUREMENT_DATA,
                            argsText: JSON.stringify(PROCUREMENT_DATA),
                        },
                    ],
                };
            }
            else if (userText.includes("kosten") || userText.includes("analyse") || userText.includes("chart")) {
                const text = "Hier ist die Kostenanalyse basierend auf den aktuellen Komponentenpreisen:";

                for (let i = 0; i < text.length; i += 5) {
                    yield { content: [{ type: "text", text: text.slice(0, i + 5) }] };
                    await new Promise((resolve) => setTimeout(resolve, 20));
                }

                await new Promise((resolve) => setTimeout(resolve, 300));

                yield {
                    content: [
                        {
                            type: "tool-call",
                            toolName: "display_cost_analysis",
                            toolCallId: "call_cost_789",
                            args: COST_ANALYSIS_DATA,
                            argsText: JSON.stringify(COST_ANALYSIS_DATA),
                        },
                    ],
                };
            }
            else {
                const response =
                    "Ich bin bereit. Du kannst 'Stückliste' oder 'Kostenanalyse' anfordern.";
                for (let i = 0; i < response.length; i += 3) {
                    yield { content: [{ type: "text", text: response.slice(0, i + 3) }] };
                    await new Promise((resolve) => setTimeout(resolve, 30));
                }
            }
        },
    });
};
