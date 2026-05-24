import { OperationsCommandCenter } from "@/components/operations/operations-command-center";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function OperationsDepartmentsPage() {
  return (
    <OperationsShell eyebrow="Municipal workflow" title="Department load">
      <OperationsCommandCenter mode="departments" />
    </OperationsShell>
  );
}
