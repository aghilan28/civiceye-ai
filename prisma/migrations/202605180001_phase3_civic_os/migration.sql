CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS incidents_location_gix
ON incidents
USING GIST (ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326));

CREATE INDEX IF NOT EXISTS detections_location_gix
ON detections
USING GIST (ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326))
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

CREATE INDEX IF NOT EXISTS incidents_road_name_trgm_idx
ON incidents
USING GIN ("roadName" gin_trgm_ops);

CREATE INDEX IF NOT EXISTS incidents_metadata_gin_idx
ON incidents
USING GIN (metadata);

CREATE INDEX IF NOT EXISTS media_assets_metadata_gin_idx
ON media_assets
USING GIN (metadata);

CREATE INDEX IF NOT EXISTS telemetry_events_payload_gin_idx
ON telemetry_events
USING GIN (payload);
