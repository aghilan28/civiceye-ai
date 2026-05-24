import { EnterpriseIntelligencePanel } from "@/components/intelligence/enterprise-intelligence-panel";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function ExecutiveAnalyticsPage() {
  return (
    <OperationsShell eyebrow="Executive analytics" title="City-scale health">
      <EnterpriseIntelligencePanel mode="executive" />
    </OperationsShell>
  );
}
