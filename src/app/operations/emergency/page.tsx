import { EnterpriseIntelligencePanel } from "@/components/intelligence/enterprise-intelligence-panel";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function OperationsEmergencyPage() {
  return (
    <OperationsShell eyebrow="Disaster response" title="Emergency coordination">
      <EnterpriseIntelligencePanel mode="emergency" />
    </OperationsShell>
  );
}
