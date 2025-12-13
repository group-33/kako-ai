import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { BOMTableTool } from "./tools/BOMTableTool";
import { ProcurementOptionsTool } from "./tools/ProcurementOptionsTool";
import type { ReadonlyJSONObject } from "assistant-stream/utils";
import { useRef } from "react";

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
  const threadIdRef = useRef<string>(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `thread_${Date.now()}`,
  );

  const runtime = useLocalRuntime({
    run: async function* ({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage || lastMessage.content[0]?.type !== "text") return;

      const userTextRaw = lastMessage.content[0].text;
      // Simuliere Nachdenken
      await new Promise((resolve) => setTimeout(resolve, 200));
      if (abortSignal.aborted) return;

      try {
        const res = await fetch(`${BACKEND_BASE_URL}/agent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_query: userTextRaw,
            thread_id: threadIdRef.current,
          }),
        });

        if (abortSignal.aborted) return;
        if (!res.ok) {
          const msg = `Backend error (${res.status}): ${await res.text()}`;
          yield { content: [{ type: "text", text: msg }] };
          return;
        }

        const data = (await res.json()) as AgentResponse;
        const content: Array<
          | { type: "text"; text: string }
          | {
              type: "tool-call";
              toolName: string;
              toolCallId: string;
              args: ReadonlyJSONObject;
              argsText: string;
            }
        > = [];

        for (const block of data.blocks) {
          if (block.type === "text") {
            content.push({ type: "text", text: block.content });
          } else if (block.type === "tool_use") {
            const args = block.data as ReadonlyJSONObject;
            content.push({
              type: "tool-call",
              toolName: block.tool_name,
              toolCallId: `call_${block.tool_name}_${Date.now()}`,
              args,
              argsText: JSON.stringify(args),
            });
          }
        }

        yield { content };
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Unknown error calling backend.";
        yield { content: [{ type: "text", text: `Network error: ${message}` }] };
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
