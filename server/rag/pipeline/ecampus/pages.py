# Tab → page-path mapping for ecampus.daiict.ac.in.
# These are PLACEHOLDER paths based on the tab labels visible in the student
# a literal path.


class Pages:
    HOME = "/Home.aspx"
    STUDENT_DETAIL = "/StudentDetail.aspx"
    REGISTRATION = "/Registration.aspx"
    COURSE_ADJUSTMENTS = "/CourseAdjustments.aspx"
    RESULT = "/Result.aspx"
    HOSTEL = "/Hostel.aspx"
    FEES = "/Fees.aspx"
    ATTENDANCE = "/Attendance.aspx"
    UTILITIES = "/Utilities.aspx"
    LOGOUT = "/Logout.aspx"

    # TODO: confirm where timetable data actually lives — it may be a
    # sub-page under Registration, a distinct tab not visible until you're
    # logged in further, or embedded inside Course Adjustments. Send a
    # screenshot of whichever tab shows weekly slot/timing data once you're
    # past login and this gets corrected to the real path.
    TIMETABLE = "/Timetable.aspx"  # best-guess placeholder
