import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { BOMTableTool } from "./tools/BOMTableTool";
import { ProcurementOptionsTool } from "./tools/ProcurementOptionsTool";
import { CostAnalysisTool } from "./tools/CostAnalysisTool";
import { useBackendRuntime } from "@/runtime/backendRuntime";

import { useThread } from "@assistant-ui/react";
import { useEffect } from "react";
import { useChatStore } from "@/store/useChatStore";

function PersistenceObserver({ threadId }: { threadId: string }) {
  const { messages } = useThread();
  const { updateThreadMessages } = useChatStore();

  useEffect(() => {
    if (threadId && messages.length > 0) {
      updateThreadMessages(threadId, messages as any[]);
    }
  }, [messages, threadId, updateThreadMessages]);

  return null;
}

export function Chat({ threadId }: { threadId: string }) {
  const runtime = useBackendRuntime(threadId);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <PersistenceObserver threadId={threadId} />
      <div className="flex h-full flex-col overflow-hidden bg-white rounded-xl border shadow-sm relative">
        <BOMTableTool />
        <ProcurementOptionsTool />
        <CostAnalysisTool />

        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}
