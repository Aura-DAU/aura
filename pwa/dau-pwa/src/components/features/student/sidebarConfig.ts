export interface NavItem {
  label: string;
  href: string;
  icon?: string;
}

export interface VerticalConfig {
  label: string;
  href: string;
  items: NavItem[];
}

export const verticalsConfig: Record<string, VerticalConfig> = {
  academics: {
    label: "Academics",
    href: "/student/academics",
    items: [
      { label: "Overview", href: "/student/academics" },
      { label: "Courses & Syllabus", href: "/student/academics/courses" },
      { label: "Program Curriculum", href: "/student/academics/curriculum" },
      { label: "Time Tables", href: "/student/academics/timetable" },
      { label: "Academic Calendar", href: "/student/academics/calendar" },
      { label: "Policies & Guidelines", href: "/student/academics/policies" },
      { label: "Hostel Rules", href: "/student/academics/hostel" },
      { label: "Examinations", href: "/student/academics/examinations" },
      { label: "Faculty Discovery", href: "/student/academics/faculty" },
      { label: "Student Services", href: "/student/academics/services" },
      { label: "Campus Services", href: "/student/academics/campus" },
      { label: "Scholarships & Support", href: "/student/academics/scholarships" },
      { label: "Wellness & Counseling", href: "/student/academics/wellness" }
    ]
  },
  cocurricular: {
    label: "Co-curricular",
    href: "/student/cocurricular",
    items: [
      { label: "Overview", href: "/student/cocurricular" },
      { label: "Student Clubs", href: "/student/cocurricular/clubs" },
      { label: "Daily Campus Events", href: "/student/cocurricular/events" },
      { label: "Student Committees", href: "/student/cocurricular/committees" }
    ]
  },
  placements: {
    label: "Placements",
    href: "/student/placements",
    items: [
      { label: "Placement Stats", href: "/student/placements" },
      { label: "Upcoming Drives", href: "/student/placements/drives" },
      { label: "Company Profiles", href: "/student/placements/companies" },
      { label: "Preparation Material", href: "/student/placements/preparation" }
    ]
  },
  "career-horizons": {
    label: "Career Horizons",
    href: "/student/career-horizons",
    items: [
      { label: "Career Fields", href: "/student/career-horizons" },
      { label: "GATE Resources", href: "/student/career-horizons/gate" },
      { label: "CAT Resources", href: "/student/career-horizons/cat" },
      { label: "UPSC Material", href: "/student/career-horizons/upsc" },
      { label: "MS / PhD Abroad", href: "/student/career-horizons/ms-phd" },
      { label: "Research & Innovation", href: "/student/career-horizons/research" },
      { label: "Other Exams", href: "/student/career-horizons/others" }
    ]
  },
  alumni: {
    label: "Alumni Network",
    href: "/student/alumni",
    items: [
      { label: "Directory", href: "/student/alumni" },
      { label: "Chapters", href: "/student/alumni/chapters" },
      { label: "Mentorship & Events", href: "/student/alumni/connect" }
    ]
  }
};

export const mainTabs = [
  { id: "academics", label: "Academics", href: "/student/academics" },
  { id: "cocurricular", label: "Co-curricular", href: "/student/cocurricular" },
  { id: "placements", label: "Placements", href: "/student/placements" },
  { id: "career-horizons", label: "Career Horizons", href: "/student/career-horizons" },
  { id: "alumni", label: "Alumni", href: "/student/alumni" }
];
