import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
// WICHTIG: Importiere das neue Tool (achte auf den Dateinamen!)
import { BOMTableTool } from "./tools/BOMTableTool";
import { ProcurementOptionsTool } from "./tools/ProcurementOptionsTool";

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
          "Verstanden. Ich habe die technischen Daten analysiert. Hier ist die vorläufige Stückliste sowie passende Beschaffungsoptionen für die kritischen Komponenten:";

        // Text streamen
        for (let i = 0; i < text.length; i += 5) {
          yield { content: [{ type: "text", text: text.slice(0, i + 5) }] };
          await new Promise((resolve) => setTimeout(resolve, 20));
        }

        await new Promise((resolve) => setTimeout(resolve, 300));

        // MOCK DATEN FÜR STÜCKLISTE (Updated Schema: 'rows')
        const bomData = {
          rows: [
            { component: "Gehäuseoberschale (ALU)", quantity: 1, unit: "Stk" },
            { component: "Platine Mainboard v2.4", quantity: 1, unit: "Stk" },
            { component: "Schrauben M4x10", quantity: 12, unit: "Stk" },
            { component: "Wärmeleitpaste", quantity: 2, unit: "g" },
            { component: "Verbindungskabel Molex", quantity: 3, unit: "Stk" },
          ],
        };

        // MOCK DATEN FÜR BESCHAFFUNG (New Schema)
        const procurementData = {
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

        // Tool Calls senden (Sequentiell oder Parallel möglich, hier als ein Block)
        yield {
          content: [
            {
              type: "tool-call",
              toolName: "display_bom_table",
              toolCallId: "call_bom_123",
              args: bomData,
              argsText: JSON.stringify(bomData),
            },
            {
              type: "tool-call",
              toolName: "display_procurement_options",
              toolCallId: "call_proc_456",
              args: procurementData,
              argsText: JSON.stringify(procurementData),
            },
          ],
        };
      } else {
        // FALLBACK: Wenn NICHT "stückliste" vorkommt
        const response =
          "Ich bin bereit. Bitte fordere eine 'Stückliste' an, um die Komponenten und Beschaffungsoptionen zu sehen.";
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
        {/* Tools registrieren */}
        <BOMTableTool />
        <ProcurementOptionsTool />

        {/* Standard Thread Komponente */}
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}
