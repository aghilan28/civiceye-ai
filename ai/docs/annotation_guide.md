# CivicEye Pothole Annotation Guide

## Target Object

Annotate only visible potholes: road-surface depressions, cavities, or broken regions with a clear boundary and operational repair relevance.

Do not label:

- shadows
- puddles without visible road damage
- oil stains
- road markings
- manhole covers
- speed bumps
- normal texture variation

## Bounding Box Rules

- Box the visible damaged cavity, not the entire lane.
- Include loose broken edges only when visually connected to the pothole.
- For multiple potholes, annotate each separately.
- For partially occluded potholes, annotate only the visible region.
- If less than 25% of the pothole is visible, mark for review instead of labeling.

## Severity Labels

Severity must be assigned per annotation.

- `minor`: small shallow cavity, low immediate traffic danger.
- `moderate`: visible cavity or spread damage, likely uncomfortable or damaging to small vehicles.
- `severe`: large or deep pothole with clear vehicle/pedestrian risk.
- `critical`: deep, wide, or multi-lane hazard requiring urgent municipal response.

## Annotation Confidence

- `1.0`: clear pothole boundary.
- `0.8`: mostly clear with partial blur or occlusion.
- `0.6`: uncertain boundary, must be reviewed.

Annotations below `0.6` should not enter training without review.
