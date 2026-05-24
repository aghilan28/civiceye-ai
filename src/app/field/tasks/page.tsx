import { FieldTaskBoard } from "@/components/field/field-task-board";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function FieldTasksPage() {
  return (
    <OperationsShell eyebrow="Field repair" title="Assigned tasks">
      <FieldTaskBoard />
    </OperationsShell>
  );
}
