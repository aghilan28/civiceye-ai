from __future__ import annotations

from backend.models.schemas import DetectionType, TenantConfig, TenantRole


class TenantIsolationService:
    def default_tenant(self) -> TenantConfig:
        return TenantConfig(
            tenant_id="blr-bbmp",
            city_name="Bengaluru",
            storage_namespace="tenants/blr-bbmp",
            allowed_roles=[
                TenantRole.platform_admin,
                TenantRole.municipality_admin,
                TenantRole.operator,
                TenantRole.field_supervisor,
                TenantRole.field_worker,
                TenantRole.auditor,
            ],
            enabled_detection_types=list(DetectionType),
            model_thresholds={issue: 0.25 for issue in DetectionType},
            branding={"primary": "#22d3ee", "accent": "#34d399"},
        )

    def authorize(self, tenant: TenantConfig, role: TenantRole, detection_type: DetectionType | None = None) -> bool:
        if role not in tenant.allowed_roles:
            return False
        if detection_type and detection_type not in tenant.enabled_detection_types:
            return False
        return True

    def storage_prefix(self, tenant_id: str, media_kind: str) -> str:
        safe_tenant = tenant_id.replace("/", "_").replace("\\", "_")
        safe_kind = media_kind.replace("/", "_").replace("\\", "_")
        return f"tenants/{safe_tenant}/{safe_kind}"


tenant_isolation_service = TenantIsolationService()
