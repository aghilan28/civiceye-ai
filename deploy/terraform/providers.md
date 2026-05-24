# Provider Matrix

## Cloud
- AWS: VPC, managed Postgres, ElastiCache Redis, S3, GPU ASG
- GCP: map VPC to VPC networks, Cloud SQL, Memorystore, GCS, GPU node pools
- Azure: map VNet, Azure Database for PostgreSQL, Azure Cache for Redis, Blob Storage, GPU VMSS
- RunPod: GPU worker pools with queue-backed scheduling
- Vast.ai: burst GPU workers with queue-backed scheduling
- Lambda Labs: inference GPU reservations with queue-backed scheduling

## Database
- Supabase: managed Postgres with PostGIS and storage
- Neon: serverless Postgres and branch-based promotion
- RDS: production primary and read replicas
- Cloud SQL: regional primary with read replicas

## Redis
- ElastiCache: primary Redis and failover
- Upstash: globally distributed queue/cache
- Redis Cloud: managed multi-region failover

## Object Storage
- S3: primary media bucket and lifecycle policies
- Cloudflare R2: CDN-friendly object storage
- Supabase Storage: tenant-scoped media store
