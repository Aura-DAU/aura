import { describe, expect, it } from "vitest"

import { toCalendarSyncAction } from "@/components/features/chat-ui/calendar-sync-presentation"

describe("toCalendarSyncAction", () => {
  it("converts the preview response into a confirmation action", () => {
    expect(
      toCalendarSyncAction(
        "This will create or update 10 recurring weekly events on your Google Calendar — one per class — with popup reminders, running until the end of the semester. Confirm to proceed.",
      ),
    ).toEqual({
      type: "timetable_sync_confirmation",
      status: "pending",
      event_count: 10,
    })
  })

  it("converts the backend queue response into a frontend sync action", () => {
    expect(
      toCalendarSyncAction(
        "Sync started in the background for 10 slots. Check status at GET /calendar/timetable/sync/status.",
      ),
    ).toEqual({
      type: "timetable_sync",
      status: "pending",
      event_count: 10,
    })
  })

  it("leaves normal assistant responses unchanged", () => {
    expect(toCalendarSyncAction("Your timetable is ready to view.")).toBeUndefined()
  })
})
