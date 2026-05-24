# Augmentation Policy

CivicEye uses conservative augmentation to simulate real municipal field conditions.

Allowed:

- mild brightness/contrast shifts
- mild blur
- rain artifacts
- shadow overlays
- JPEG compression
- camera perspective changes
- low-light simulation

Rejected:

- transformations that make potholes invisible
- extreme rotations
- unrealistic color shifts
- synthetic roads with no real-world appearance
- excessive rain or blur that destroys annotation validity

Every augmentation profile must be versioned and linked to experiments.
