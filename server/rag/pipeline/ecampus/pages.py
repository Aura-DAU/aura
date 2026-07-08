"""
Tab → page-path mapping for ecampus.daiict.ac.in.

ALL paths confirmed from real portal HTML (July 2026).
Extracted from the JavaScript menu arrays in every page's source.
Base URL: https://ecampus.daiict.ac.in
"""


class Pages:
    # ── Core student pages (confirmed) ────────────────────────────────────
    HOME                  = "/webapp/intranet/edu/student/DefaultStudentHomePage.jsp"
    STUDENT_DETAIL        = "/webapp/intranet/StudentDetailEditServlet"
    REGISTRATION_LIST     = "/webapp/intranet/StudentRegistrationListServlet"
    REGISTRATION_EDIT     = "/webapp/intranet/StudentRegistrationEditServlet"   # POST with stdid + SemesterID
    COURSE_DROP           = "/webapp/intranet/CourseDropListServlet"
    GRADE_SEMESTER_LIST   = "/webapp/intranet/GradeSemesterListServlet"
    GRADE_COURSE_LIST     = "/webapp/intranet/GradeCourseListServlet"           # POST with stdid + SemesterID

    # ── Hostel submenu (confirmed from menu JS) ────────────────────────────
    BULLETIN_BOARD        = "/webapp/intranet/BulletinListDisplayServlet"
    HOSTEL_COMPLAINTS     = "/webapp/intranet/StudentComplainListServlet"
    HOSTEL_LEAVES         = "/webapp/intranet/HostelStudentLeavesListServlet"
    HOSTEL_VISITOR_ROOM   = "/webapp/intranet/HostelVisitRoomBookingsListServlet"
    HOSTEL_RULES          = "/webapp/intranet/HostelPolicyListDisplayServlet"

    # ── Fees (confirmed from menu JS) ─────────────────────────────────────
    FEE_RECEIPTS_CANDIDATE = "/webapp/intranet/CandidateReceiptsViewServlet"
    FEE_RECEIPTS_STUDENT   = "/webapp/intranet/SemSelector?target=StudentReceiptsViewServlet&actiontext=List Semesters"

    # ── Attendance (confirmed — NOTE: real portal has typo "Attandance") ──
    ATTENDANCE_LIST       = "/webapp/intranet/AttandanceSemesterListServlet"    # typo is intentional

    # ── Utilities ─────────────────────────────────────────────────────────
    CHANGE_PASSWORD       = "/webapp/intranet/edu/ChangePassword.jsp"

    # ── Logout (confirmed from menu JS) ───────────────────────────────────
    LOGOUT                = "/webapp/intranet/LoginServlet?logout=true"

    # ── Grade card navigation ──────────────────────────────────────────────
    # To get grade card for a specific semester, POST to GRADE_COURSE_LIST
    # with form fields: stdid=<STDID> and SemesterID=<SEMESTERID>
    # Both values come from parse_grade_semester_list() results.
    # Example: stdid=12436, SemesterID=1455 → Semester IV grade card