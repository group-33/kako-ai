import { useEffect } from "react";
import { makeAssistantToolUI } from "@assistant-ui/react";
import { useMetricsStore } from "@/store/useMetricsStore";

type FeasibilityMetricArgs = {
  event_id?: string;
};

const FeasibilityMetric = ({ args }: { args: FeasibilityMetricArgs }) => {
  const registerFeasibilityCheck = useMetricsStore(s => s.registerFeasibilityCheck);

  useEffect(() => {
    if (args?.event_id) {
      registerFeasibilityCheck(args.event_id);
    }
  }, [args?.event_id, registerFeasibilityCheck]);

  return null;
};

export const FeasibilityMetricTool = makeAssistantToolUI({
  toolName: "track_feasibility_check",
  render: ({ args }) => {
    return <FeasibilityMetric args={args as FeasibilityMetricArgs} />;
  },
});
