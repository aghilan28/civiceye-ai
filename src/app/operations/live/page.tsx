import { OperationsCommandCenter } from "@/components/operations/operations-command-center";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function OperationsLivePage() {
  return (
    <OperationsShell eyebrow="Municipal command" title="Live operations center">
      <OperationsCommandCenter mode="live" />
    </OperationsShell>
  );
}
