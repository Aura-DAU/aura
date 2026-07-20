"""
pipeline.timetable — AURA-owned student timetable subsystem.

Unlike everything under pipeline/ecampus (which is strictly read-only
against the ERP DB), the timetable is data AURA itself owns end to end:
a shared cohort schedule (timetable_master, admin-managed) plus per-student
overrides (timetable_overrides) that only the student who created them can
see or change. This is why it lives in its own package with its own tool
registry instead of being folded into pipeline/ecampus.
"""
