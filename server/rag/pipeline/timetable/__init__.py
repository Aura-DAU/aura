"""
pipeline.timetable — AURA-owned student timetable subsystem.

The timetable is data AURA itself owns end to end:
a shared cohort schedule (timetable_master, admin-managed) plus per-student
overrides (timetable_overrides) that only the student who created them can
see or change. agent.py is the tool-calling agent the chat graph uses for
these reads/writes and for Google Calendar sync.
"""
