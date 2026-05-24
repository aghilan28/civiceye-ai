import { EnterpriseIntelligencePanel } from "@/components/intelligence/enterprise-intelligence-panel";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function InfrastructureAnalyticsPage() {
  return (
    <OperationsShell eyebrow="Infrastructure analytics" title="AI model and asset intelligence">
      <EnterpriseIntelligencePanel mode="infrastructure" />
    </OperationsShell>
  );
}
