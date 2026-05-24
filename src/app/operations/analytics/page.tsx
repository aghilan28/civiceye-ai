import { OperationsCommandCenter } from "@/components/operations/operations-command-center";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function OperationsAnalyticsPage() {
  return (
    <OperationsShell eyebrow="Civic analytics" title="Road intelligence">
      <OperationsCommandCenter mode="analytics" />
    </OperationsShell>
  );
}
