import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
// WICHTIG: Importiere das neue Tool (achte auf den Dateinamen!)
import { BOMTableTool } from "./tools/BOMTableTool";

export function Chat() {
  const runtime = useLocalRuntime({
    run: async function* ({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage || lastMessage.content[0]?.type !== "text") return;

      // Alles in Kleinbuchstaben umwandeln für den Vergleich
      const userText = lastMessage.content[0].text.toLowerCase();

      // Simuliere Nachdenken
      await new Promise((resolve) => setTimeout(resolve, 600));
      if (abortSignal.aborted) return;

      // --- LOGIK WEICHE ---

      // TRIGGER: Reagiert nur auf das Wort "stückliste"
      if (userText.includes("stückliste")) {
        const text =
          "Verstanden. Ich habe die technischen Daten analysiert. Hier ist die vorläufige Stückliste für die Fertigung:";

        // Text streamen
        for (let i = 0; i < text.length; i += 5) {
          yield { content: [{ type: "text", text: text.slice(0, i + 5) }] };
          await new Promise((resolve) => setTimeout(resolve, 20));
        }

        await new Promise((resolve) => setTimeout(resolve, 300));

        // MOCK DATEN FÜR STÜCKLISTE
        const bomData = {
          data: [
            { component: "Gehäuseoberschale (ALU)", quantity: 1, unit: "Stk" },
            { component: "Platine Mainboard v2.4", quantity: 1, unit: "Stk" },
            { component: "Schrauben M4x10", quantity: 12, unit: "Stk" },
            { component: "Wärmeleitpaste", quantity: 2, unit: "g" },
            { component: "Verbindungskabel Molex", quantity: 3, unit: "Stk" },
          ],
        };

        // Tool Call senden
        yield {
          content: [
            {
              type: "tool-call",
              toolName: "display_bom_table", // Muss mit BOMTableTool übereinstimmen
              toolCallId: "call_bom_123",
              args: bomData,
              argsText: JSON.stringify(bomData),
            },
          ],
        };
      } else {
        // FALLBACK: Wenn NICHT "stückliste" vorkommt
        const response =
          "Ich bin bereit. Bitte fordere eine 'Stückliste' an, um die Komponenten zu sehen.";
        for (let i = 0; i < response.length; i += 3) {
          yield { content: [{ type: "text", text: response.slice(0, i + 3) }] };
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
