import { EnterpriseIntelligencePanel } from "@/components/intelligence/enterprise-intelligence-panel";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function PredictionsAnalyticsPage() {
  return (
    <OperationsShell eyebrow="Predictive intelligence" title="Autonomous risk forecast">
      <EnterpriseIntelligencePanel mode="predictions" />
    </OperationsShell>
  );
}
