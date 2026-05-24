import { OperationsCommandCenter } from "@/components/operations/operations-command-center";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function OperationsIncidentsPage() {
  return (
    <OperationsShell eyebrow="Incident management" title="Civic incident queue">
      <OperationsCommandCenter mode="incidents" />
    </OperationsShell>
  );
}
