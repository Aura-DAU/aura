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
    href: "/academics",
    items: [
      { label: "Overview", href: "/academics" },
      { label: "Courses & Syllabus", href: "/academics/courses" },
      { label: "Program Curriculum", href: "/academics/curriculum" },
      { label: "Time Tables", href: "/academics/timetable" },
      { label: "Academic Calendar", href: "/academics/calendar" },
      { label: "Policies & Guidelines", href: "/academics/policies" },
      { label: "Hostel Rules", href: "/academics/hostel" },
      { label: "Examinations", href: "/academics/examinations" },
      { label: "Faculty Discovery", href: "/academics/faculty" },
      { label: "Student Services", href: "/academics/services" },
      { label: "Campus Services", href: "/academics/campus" },
      { label: "Scholarships & Support", href: "/academics/scholarships" },
      { label: "Wellness & Counseling", href: "/academics/wellness" }
    ]
  },
  "co-curricular": {
    label: "Co-curricular",
    href: "/co-curricular",
    items: [
      { label: "Overview", href: "/co-curricular" },
      { label: "Student Clubs", href: "/co-curricular/clubs" },
      { label: "Daily Campus Events", href: "/co-curricular/events" },
      { label: "Student Committees", href: "/co-curricular/committees" }
    ]
  },
  placements: {
    label: "Placements",
    href: "/placements",
    items: [
      { label: "Placement Stats", href: "/placements" },
      { label: "Upcoming Drives", href: "/placements/drives" },
      { label: "Company Profiles", href: "/placements/companies" },
      { label: "Preparation Material", href: "/placements/preparation" }
    ]
  },
  "career-horizons": {
    label: "Career Horizons",
    href: "/career-horizons",
    items: [
      { label: "Career Fields", href: "/career-horizons" },
      { label: "GATE Resources", href: "/career-horizons/gate" },
      { label: "CAT Resources", href: "/career-horizons/cat" },
      { label: "UPSC Material", href: "/career-horizons/upsc" },
      { label: "MS / PhD Abroad", href: "/career-horizons/ms-phd" },
      { label: "Research & Innovation", href: "/career-horizons/research" },
      { label: "Other Exams", href: "/career-horizons/others" }
    ]
  },
  alumni: {
    label: "Alumni Network",
    href: "/alumni",
    items: [
      { label: "Directory", href: "/alumni" },
      { label: "Chapters", href: "/alumni/chapters" },
      { label: "Mentorship & Events", href: "/alumni/connect" }
    ]
  }
};

export const mainTabs = [
  { id: "academics", label: "Academics", href: "/academics" },
  { id: "co-curricular", label: "Co-curricular", href: "/co-curricular" },
  { id: "placements", label: "Placements", href: "/placements" },
  { id: "career-horizons", label: "Career Horizons", href: "/career-horizons" },
  { id: "alumni", label: "Alumni", href: "/alumni" }
];
