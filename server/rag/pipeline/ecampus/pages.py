"""
Tab → page-path mapping for ecampus.daiict.ac.in.

These are PLACEHOLDER paths based on the tab labels visible in the student
portal screenshot (Home, Student Detail, Registration, Course Adjustments,
Result, Hostel, Fees, Attendance, Utilities, LOGOUT). Classic ASP.NET sites
of this vintage commonly use a flat *.aspx naming scheme like this, but the
exact filenames need to be confirmed from the live URL bar or page source —
update the values below once you have them, nothing else in the codebase
needs to change since every other module references these constants, never
a literal path.
"""


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
