import { OperationsCommandCenter } from "@/components/operations/operations-command-center";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function FieldHistoryPage() {
  return (
    <OperationsShell eyebrow="Repair lifecycle" title="Field history">
      <OperationsCommandCenter mode="field" />
    </OperationsShell>
  );
}
