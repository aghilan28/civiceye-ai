import { EnterpriseIntelligencePanel } from "@/components/intelligence/enterprise-intelligence-panel";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function DistrictAnalyticsPage() {
  return (
    <OperationsShell eyebrow="District analytics" title="Risk and SLA degradation">
      <EnterpriseIntelligencePanel mode="districts" />
    </OperationsShell>
  );
}
