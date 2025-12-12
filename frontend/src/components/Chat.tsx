import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { BOMTableTool } from "./tools/BOMTableTool";
import type { ReadonlyJSONObject } from "assistant-stream/utils";

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

type TextBlock = {
  type: "text";
  content: string;
};

type ToolUseBlock = {
  type: "tool_use";
  tool_name: string;
  data: ReadonlyJSONObject;
};

type AgentResponse = {
  response_id: string;
  created_at: string;
  blocks: Array<TextBlock | ToolUseBlock>;
};

export function Chat() {
  const runtime = useLocalRuntime({
    run: async function* ({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage || lastMessage.content[0]?.type !== "text") return;

      const userTextRaw = lastMessage.content[0].text;
      const userText = userTextRaw.toLowerCase();

      // Simuliere Nachdenken
      await new Promise((resolve) => setTimeout(resolve, 600));
      if (abortSignal.aborted) return;

      // TRIGGER: Reagiert nur auf das Wort "stückliste"
      if (userText.includes("stückliste")) {
        const text =
          "Verstanden. Ich habe die technischen Daten analysiert. Hier ist die vorläufige Stückliste für die Fertigung:";

        // Text streamen wie zuvor
        for (let i = 0; i < text.length; i += 5) {
          if (abortSignal.aborted) return;
          yield { content: [{ type: "text", text: text.slice(0, i + 5) }] };
          await new Promise((resolve) => setTimeout(resolve, 20));
        }

        await new Promise((resolve) => setTimeout(resolve, 300));
        if (abortSignal.aborted) return;

        // NEU: Versuche echte BOM-Extraktion über das Backend, falls ein Pfad erkennbar ist
        const pathMatch = userTextRaw.match(
          /(?:\/[^\s]+)+\.(?:png|jpg|jpeg|pdf)/i,
        );
        const filenameForBackend = pathMatch?.[0];

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
              const data = (await res.json()) as AgentResponse;
              const bomBlock = data.blocks.find(
                (b): b is ToolUseBlock =>
                  b.type === "tool_use" &&
                  b.tool_name === "display_bom_table",
              );

              if (bomBlock) {
                const toolCallId = `call_bom_${Date.now()}`;

                // Backend sends { rows: [...], source_document?: string }.
                // The BOMTableTool expects args.data to be an array of rows.
                const rows = Array.isArray(
                  (bomBlock.data as { rows?: ReadonlyJSONObject[] }).rows,
                )
                  ? ((bomBlock.data as { rows: ReadonlyJSONObject[] }).rows ??
                    [])
                  : [];

                const args: ReadonlyJSONObject = { data: rows };

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
            // Bei Fehler einfach auf Mock-Daten zurückfallen
          }
        }

        // FALLBACK: Mock-Daten für Stückliste wie früher
        const bomData = {
          data: [
            { component: "Gehäuseoberschale (ALU)", quantity: 1, unit: "Stk" },
            { component: "Platine Mainboard v2.4", quantity: 1, unit: "Stk" },
            { component: "Schrauben M4x10", quantity: 12, unit: "Stk" },
            { component: "Wärmeleitpaste", quantity: 2, unit: "g" },
            { component: "Verbindungskabel Molex", quantity: 3, unit: "Stk" },
          ],
        };

        yield {
          content: [
            {
              type: "tool-call",
              toolName: "display_bom_table",
              toolCallId: "call_bom_123",
              args: bomData,
              argsText: JSON.stringify(bomData),
            },
          ],
        };
      } else {
        // FALLBACK: Wenn NICHT "stückliste" vorkommt – alter Mock-Text
        const response =
          "Ich bin bereit. Bitte fordere eine 'Stückliste' an, um die Komponenten zu sehen.";
        for (let i = 0; i < response.length; i += 3) {
          if (abortSignal.aborted) return;
          yield {
            content: [{ type: "text", text: response.slice(0, i + 3) }],
          };
          await new Promise((resolve) => setTimeout(resolve, 30));
        }
      }
    },
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex h-full flex-col overflow-hidden bg-white rounded-xl border shadow-sm relative">
        {/* Hier das neue Tool registrieren */}
        <BOMTableTool />

        {/* Standard Thread Komponente */}
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}
