import { useLocalRuntime } from "@assistant-ui/react";
import type {
  Attachment,
  CompleteAttachment,
  PendingAttachment,
  ThreadAssistantMessagePart,
} from "@assistant-ui/react";
import type { ReadonlyJSONObject } from "assistant-stream/utils";
import { useChatStore } from "@/store/useChatStore";

type TextBlock = { type: "text"; content: string };
type ToolUseBlock = { type: "tool_use"; tool_name: string; data: unknown };
type AgentResponse = { blocks?: Array<TextBlock | ToolUseBlock> };

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

export const useBackendRuntime = (threadIdParam?: string) => {
  const { activeThreadId, threads, renameThread, modelId } = useChatStore();
  const threadId = threadIdParam ?? activeThreadId ?? "default";
  const activeThread = threads.find((t) => t.id === threadId);
  const initialMessages = activeThread?.messages || [];

  return useLocalRuntime({
    run: async function* ({ messages, abortSignal }) {
      console.log("Runtime received messages:", messages);
      const lastMessage = messages[messages.length - 1];
      console.log("Last message full object:", lastMessage);

      const textPart = lastMessage?.content.find((part) => part.type === "text");
      const userText = textPart && "text" in textPart ? textPart.text.trim() : "";
      const attachments = (lastMessage?.attachments ?? []) as ReadonlyArray<Attachment>;
      console.log("Attachments array:", attachments);

      const firstAttachment = attachments?.[0];
      console.log("First attachment:", firstAttachment);
      const file = firstAttachment?.file as File | undefined;
      console.log("Extracted file object from attachment:", file);

      if (!userText && !file) {
        console.log("No text and no file, returning");
        return;
      }

      const userMessages = messages.filter(m => m.role === 'user');
      const currentThread = useChatStore.getState().threads.find((t) => t.id === threadId);
      if (userMessages.length === 1 && currentThread && userText) {
        const isDefaultTitle = currentThread.title.startsWith("New Chat") || currentThread.title.startsWith("Neuer Chat");
        if (isDefaultTitle) {
          try {
            const titleResponse = await fetch(`${BACKEND_BASE_URL}/chat/title`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                user_query: userText,
                model_id: modelId,
              }),
              signal: abortSignal,
            });
            if (titleResponse.ok) {
              const data = await titleResponse.json();
              if (data?.title) {
                await renameThread(currentThread.id, data.title);
              }
            }
          } catch (error) {
            if (!abortSignal.aborted) {
              console.warn("Title generation failed:", error);
            }
          }
        }
      }

      let response: Response;
      try {
        let body: BodyInit;
        const headers: HeadersInit = {};

        if (file) {
          console.log("Preparing FormData with file:", file.name, file.type, file.size);
          const formData = new FormData();
          formData.append("user_query", userText);
          formData.append("thread_id", threadId);
          if (modelId) formData.append("model_id", modelId);
          formData.append("file", file);
          body = formData;
        } else {
          headers["Content-Type"] = "application/json";
          body = JSON.stringify({
            user_query: userText,
            thread_id: threadId,
            model_id: modelId,
          });
        }

        response = await fetch(`${BACKEND_BASE_URL}/agent`, {
          method: "POST",
          headers,
          body,
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
  }, {
    initialMessages,
    adapters: {
      attachments: {
        accept: "*/*",
        add: async ({ file }: { file: File }) => ({
          id: Math.random().toString(36).slice(2),
          file,
          type: file.type.startsWith("image/") ? "image" : "file",
          status: { type: "requires-action", reason: "composer-send" } as const,
          name: file.name,
          contentType: file.type,
        }),
        remove: async () => { },
        send: async (attachment: PendingAttachment): Promise<CompleteAttachment> => ({
          ...attachment,
          status: { type: "complete" },
          content: [],
        }),
      },
    },
  });
};
