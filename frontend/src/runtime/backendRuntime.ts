import { useMemo } from "react";
import { useLocalRuntime } from "@assistant-ui/react";
import type {
  Attachment,
  CompleteAttachment,
  PendingAttachment,
  ThreadAssistantMessagePart,
} from "@assistant-ui/react";
import type { ReadonlyJSONObject } from "assistant-stream/utils";
import { useChatStore } from "@/store/useChatStore";
import { supabase } from "@/lib/supabase";

type TextBlock = { type: "text"; content: string };
type ToolUseBlock = { type: "tool_use"; tool_name: string; data: unknown };
type AgentResponse = { blocks?: Array<TextBlock | ToolUseBlock> };

const BACKEND_BASE_URL =
  (import.meta as ImportMeta & { env: { VITE_BACKEND_URL?: string } }).env
    .VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

export const useBackendRuntime = (threadIdParam?: string) => {
  const activeThreadId = useChatStore(state => state.activeThreadId);
  const threadId = threadIdParam ?? activeThreadId ?? "default";
  const modelId = useChatStore(state => state.modelId);
  const isImageFile = (file: File) =>
    file.type.startsWith("image/") ||
    /\.(png|jpe?g|gif|webp|bmp|tiff?|heic|heif|svg)$/i.test(file.name);
  const fileToDataUrl = (file: File) =>
    new Promise<string | null>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = typeof reader.result === "string" ? reader.result : null;
        resolve(result);
      };
      reader.onerror = () => reject(reader.error ?? new Error("Failed to read file"));
      reader.readAsDataURL(file);
    });

  // Fetch initial messages only when threadId changes to avoid reactive loops
  const initialMessages = useMemo(() => {
    return useChatStore.getState().threads.find(t => t.id === threadId)?.messages || [];
  }, [threadId]);

  return useLocalRuntime({
    run: async function* ({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];
      const textPart = lastMessage?.content.find((part) => part.type === "text");
      const userText = textPart && "text" in textPart ? textPart.text.trim() : "";
      const attachments = (lastMessage?.attachments ?? []) as ReadonlyArray<Attachment>;
      const firstAttachment = attachments?.[0];
      const file = firstAttachment?.file as File | undefined;

      if (!userText && !file) {
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
                await useChatStore.getState().renameThread(currentThread.id, data.title);
              }
            }
          } catch {
            // Title generation failed, but we don't log it anymore.
          }
        }
      }

      let response: Response;
      try {
        let body: BodyInit;
        const headers: HeadersInit = {};

        if (file) {
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

        const session = await supabase.auth.getSession();
        const token = session.data.session?.access_token;
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
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
        add: async ({ file }: { file: File }) => {
          const isImage = isImageFile(file);
          const content = isImage
            ? (() => {
              return fileToDataUrl(file).then((dataUrl) =>
                dataUrl ? [{ type: "image" as const, image: dataUrl }] : []
              );
            })()
            : Promise.resolve([]);
          return {
            id: Math.random().toString(36).slice(2),
            file,
            type: isImage ? "image" : "file",
            status: { type: "requires-action", reason: "composer-send" } as const,
            name: file.name,
            contentType: file.type,
            content: await content,
          };
        },
        remove: async () => { },
        send: async (attachment: PendingAttachment): Promise<CompleteAttachment> => {
          return {
            ...attachment,
            status: { type: "complete" },
            content: attachment.content ?? [],
          };
        },
      },
    },
  });
};
