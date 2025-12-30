import { useLocalRuntime } from "@assistant-ui/react";
import type { ThreadAssistantMessagePart } from "@assistant-ui/react";
import type { ReadonlyJSONObject } from "assistant-stream/utils";
import { useChatStore } from "@/store/useChatStore";

type TextBlock = { type: "text"; content: string };
type ToolUseBlock = { type: "tool_use"; tool_name: string; data: unknown };
type AgentResponse = { blocks?: Array<TextBlock | ToolUseBlock> };

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

export const useBackendRuntime = () => {
  const threadId = useChatStore((state) => state.activeThreadId) ?? "default";

  return useLocalRuntime({
    run: async function* ({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];
      const textPart = lastMessage?.content.find((part) => part.type === "text");
      const userText =
        textPart && "text" in textPart ? textPart.text.trim() : "";

      if (!userText) return;

      let response: Response;
      try {
        response = await fetch(`${BACKEND_BASE_URL}/agent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_query: userText,
            thread_id: threadId,
          }),
          signal: abortSignal,
        });
      } catch (error) {
        if (abortSignal.aborted) return;
        const message =
          error instanceof Error ? error.message : "Unknown error";
        yield {
          content: [
            {
              type: "text",
              text: `Backend request failed: ${message}`,
            },
          ],
        };
        return;
      }

      if (!response.ok) {
        const errorText = await response.text();
        yield {
          content: [
            {
              type: "text",
              text: `Backend error: ${errorText || response.statusText}`,
            },
          ],
        };
        return;
      }

      const data = (await response.json()) as AgentResponse;
      const content: ThreadAssistantMessagePart[] = [];

      let toolIndex = 0;
      for (const block of data.blocks ?? []) {
        if (block.type === "text") {
          content.push({ type: "text", text: block.content });
          continue;
        }

        if (block.type === "tool_use") {
          const toolCallId = `call_${block.tool_name}_${Date.now()}_${toolIndex++}`;
          content.push({
            type: "tool-call",
            toolName: block.tool_name,
            toolCallId,
            args: block.data as ReadonlyJSONObject,
            argsText: JSON.stringify(block.data),
          });
        }
      }

      if (content.length) {
        yield { content };
      }
    },
  });
};
