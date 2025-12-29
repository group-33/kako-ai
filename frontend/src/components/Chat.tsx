import { Thread } from "@/components/assistant-ui/thread";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { BOMTableTool } from "./tools/BOMTableTool";
import { ProcurementOptionsTool } from "./tools/ProcurementOptionsTool";
import { CostAnalysisTool } from "./tools/CostAnalysisTool";
import { useMockRuntime } from "@/mocks/mockRuntime";

export function Chat() {
  const runtime = useMockRuntime();

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex h-full flex-col overflow-hidden bg-white rounded-xl border shadow-sm relative">
        {/* Tools registrieren */}
        <BOMTableTool />
        <ProcurementOptionsTool />
        <CostAnalysisTool />

        {/* Standard Thread Komponente */}
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}
