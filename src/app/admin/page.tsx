import { AiObservabilityPanel } from "@/components/admin/ai-observability-panel";
import { DeploymentHealthPanel } from "@/components/admin/deployment-health-panel";
import { PageHeader } from "@/components/product/page-header";
import { Button } from "@/components/ui/button";

export default function AdminPage() {
  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-7xl">
        <PageHeader
          eyebrow="Municipal administration"
          title="Enterprise control plane"
          description="Model health, deployment readiness, role governance, and municipality-scale operating telemetry."
          action={<Button variant="gradient">Export audit pack</Button>}
        />
        <div className="mt-8 grid gap-5">
          <DeploymentHealthPanel />
          <AiObservabilityPanel />
        </div>
      </div>
    </section>
  );
}
