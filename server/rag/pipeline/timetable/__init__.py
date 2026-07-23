"""
pipeline.timetable -- AURA-owned student and faculty timetable subsystem.

Unlike everything under pipeline/ecampus (which is strictly read-only
against the ERP DB), the timetable is data AURA itself owns end to end:
a shared cohort schedule (timetable_master, admin-managed via XLSX import)
plus per-student overrides (timetable_overrides) that only the student who
created them can see or change.

Faculty get a read-only aggregated view showing all their classes across
every batch/section/year.
"""
