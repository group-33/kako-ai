import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { BOMTableTool } from "./tools/BOMTableTool";
import { ProcurementOptionsTool } from "./tools/ProcurementOptionsTool";
import { CostAnalysisTool } from "./tools/CostAnalysisTool";
import { FeasibilityMetricTool } from "./tools/FeasibilityMetricTool";
import { useBackendRuntime } from "@/runtime/backendRuntime";

import { useAssistantState } from "@assistant-ui/react";
import { useEffect, memo } from "react";
import { useChatStore } from "@/store/useChatStore";

function PersistenceObserver({ threadId }: { threadId: string }) {
  const messages = useAssistantState(({ thread }) => thread.messages);
  const updateThreadMessages = useChatStore(state => state.updateThreadMessages);

  useEffect(() => {
    if (threadId && messages.length > 0) {
      void updateThreadMessages(threadId, messages);
    }
  }, [messages, threadId, updateThreadMessages]);

  return null;
}

export const Chat = memo(function Chat({ threadId, initialDraft }: { threadId: string; initialDraft?: string }) {
  const runtime = useBackendRuntime(threadId);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <PersistenceObserver threadId={threadId} />
      <div className="flex h-full flex-col overflow-hidden bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-800 shadow-2xl relative">
        <BOMTableTool />
        <ProcurementOptionsTool />
        <CostAnalysisTool />
        <FeasibilityMetricTool />

        <Thread threadId={threadId} initialDraft={initialDraft} />
      </div>
    </AssistantRuntimeProvider>
  );
});
