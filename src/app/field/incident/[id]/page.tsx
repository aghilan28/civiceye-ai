import { FieldTaskBoard } from "@/components/field/field-task-board";
import { OperationsShell } from "@/components/operations/operations-shell";

export default async function FieldIncidentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <OperationsShell eyebrow="Repair task" title="Incident work order">
      <FieldTaskBoard incidentId={id} />
    </OperationsShell>
  );
}
