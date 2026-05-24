import { EnterpriseIntelligencePanel } from "@/components/intelligence/enterprise-intelligence-panel";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function OperationsDistrictsPage() {
  return (
    <OperationsShell eyebrow="District intelligence" title="Degradation and workload">
      <EnterpriseIntelligencePanel mode="districts" />
    </OperationsShell>
  );
}
