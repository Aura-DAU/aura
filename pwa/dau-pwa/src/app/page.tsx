import Link from "next/link";
import Image from "next/image";

const portalSections = [
  {
    title: "Academics",
    desc: "Courses, timetables, calendar, policies, faculty and hostel guidelines.",
    href: "/student/academics",
    iconBg: "bg-orange-100 border border-orange-200 text-[#E8400C]",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    title: "Placements",
    desc: "Upcoming drives, company profiles, placement stats and preparation resources.",
    href: "/student/placements",
    iconBg: "bg-emerald-100 border border-emerald-200 text-emerald-600",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0" />
      </svg>
    ),
  },
  {
    title: "Co-curricular",
    desc: "Student clubs, committees, events and campus activities.",
    href: "/student/cocurricular",
    iconBg: "bg-purple-100 border border-purple-200 text-purple-600",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
      </svg>
    ),
  },
  {
    title: "Career Horizons",
    desc: "Resources for GATE, CAT, UPSC, MS/PhD abroad and research.",
    href: "/student/career-horizons",
    iconBg: "bg-amber-100 border border-amber-200 text-amber-600",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
      </svg>
    ),
  },
  {
    title: "Alumni Network",
    desc: "Connect with alumni, explore chapters and find mentorship.",
    href: "/student/alumni",
    iconBg: "bg-rose-100 border border-rose-200 text-rose-600",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
      </svg>
    ),
  },
  {
    title: "AURA AI Assistant",
    desc: "Ask anything about campus life, policies, clubs or hostel rules.",
    href: "/student/chat",
    iconBg: "bg-orange-100 border border-orange-200 text-[#E8400C]",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] font-sans">

      {/* ── TOP NAV ── */}
      <header className="bg-white border-b border-[#E2E8F0] px-6 py-4 flex items-center justify-between shadow-sm">
        <Image
          src="/dau_logo.jpg"
          alt="Dhirubhai Ambani University"
          width={180}
          height={44}
          priority
          className="h-11 w-auto object-contain"
        />
        <div className="flex items-center gap-3">
          <Link
            href="/student/chat"
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-[#E8400C] transition-colors px-3 py-2 hidden sm:flex"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Ask AURA
          </Link>
          <Link
            href="/student/academics"
            className="text-xs font-black bg-[#E8400C] hover:bg-[#D7380A] text-white px-5 py-2.5 rounded-full transition-colors shadow-md shadow-[#E8400C]/20"
          >
            Enter Portal
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-10">

        {/* ── WELCOME + LOGIN SPLIT ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">

          {/* LEFT — Welcome Card */}
          <div className="bg-white border border-[#E2E8F0] rounded-[24px] p-8 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-6">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Student Portal · 2025–26</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-black text-slate-900 leading-tight mb-3">
                Welcome to<br />
                <span className="text-[#E8400C]">DAU Student</span><br />
                Portal
              </h1>
              <p className="text-sm text-slate-500 font-medium leading-relaxed mb-6">
                Your one-stop destination for academics, placements, co-curricular
                activities, career resources and campus life at Dhirubhai Ambani University.
              </p>

              {/* Quick stats */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                {[
                  { value: "25+", label: "Years" },
                  { value: "6000+", label: "Students" },
                  { value: "200+", label: "Recruiters" },
                ].map((s) => (
                  <div key={s.label} className="bg-slate-50 border border-[#E2E8F0] rounded-2xl p-3 text-center">
                    <p className="text-lg font-black text-slate-900">{s.value}</p>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>

            <Link
              href="/student/academics"
              className="flex items-center justify-center gap-2 bg-[#E8400C] hover:bg-[#D7380A] text-white text-sm font-black py-3.5 px-6 rounded-[16px] transition-colors shadow-md shadow-[#E8400C]/20 w-full"
            >
              Go to Student Portal
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>

          {/* RIGHT — Sign In Card */}
          <div className="bg-white border border-[#E2E8F0] rounded-[24px] p-8 shadow-sm">
            <div className="mb-6">
              <h2 className="text-xl font-black text-slate-900 mb-1">Sign In</h2>
              <p className="text-xs text-slate-500 font-medium">
                Use your DAU student credentials to access the portal.
              </p>
            </div>

            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              {/* Student ID */}
              <div>
                <label className="block text-xs font-black text-slate-700 mb-1.5 uppercase tracking-wide">
                  Student ID
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none">
                    <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    placeholder="e.g. 202201234"
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-[#E2E8F0] rounded-[14px] text-sm text-slate-800 placeholder-slate-400 font-medium focus:outline-none focus:border-[#E8400C] focus:ring-1 focus:ring-[#E8400C]/20 transition-colors"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-black text-slate-700 mb-1.5 uppercase tracking-wide">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none">
                    <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                  </div>
                  <input
                    type="password"
                    placeholder="Enter your password"
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-[#E2E8F0] rounded-[14px] text-sm text-slate-800 placeholder-slate-400 font-medium focus:outline-none focus:border-[#E8400C] focus:ring-1 focus:ring-[#E8400C]/20 transition-colors"
                  />
                </div>
              </div>

              {/* Forgot password */}
              <div className="flex justify-end">
                <button type="button" className="text-xs font-semibold text-[#E8400C] hover:underline">
                  Forgot password?
                </button>
              </div>

              {/* Submit */}
              <Link
                href="/student/academics"
                className="block w-full bg-[#E8400C] hover:bg-[#D7380A] text-white text-sm font-black py-3.5 px-6 rounded-[16px] transition-colors shadow-md shadow-[#E8400C]/20 text-center"
              >
                Sign In to Portal
              </Link>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px bg-[#E2E8F0]" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">or</span>
              <div className="flex-1 h-px bg-[#E2E8F0]" />
            </div>

            {/* AURA shortcut */}
            <Link
              href="/student/chat"
              className="flex items-center justify-center gap-2 w-full bg-orange-50 hover:bg-orange-100 border border-orange-200 text-[#E8400C] text-xs font-black py-3 px-6 rounded-[16px] transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Continue as Guest · Ask AURA
            </Link>

            <p className="text-[10px] text-slate-400 font-medium text-center mt-4 leading-relaxed">
              Your credentials are managed by the DAU IT department.<br />
              Contact <span className="text-slate-600 font-semibold">itsupport@daiict.ac.in</span> for access issues.
            </p>
          </div>
        </div>

        {/* ── QUICK ACCESS ── */}
        <section>
          <div className="border-b border-[#E2E8F0] pb-4 mb-6">
            <h2 className="text-xl font-black text-slate-900">Quick Access</h2>
            <p className="text-xs text-slate-500 font-medium mt-1">
              Jump directly to any section of the student portal.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {portalSections.map((section) => (
              <div
                key={section.title}
                className="flex flex-col bg-white border border-[#E2E8F0] rounded-[24px] p-6 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className={`w-12 h-12 rounded-[16px] flex items-center justify-center mb-4 ${section.iconBg}`}>
                  {section.icon}
                </div>
                <h3 className="text-base font-black text-slate-900 mb-1">{section.title}</h3>
                <p className="text-xs text-slate-500 font-medium leading-relaxed flex-1">{section.desc}</p>
                <Link
                  href={section.href}
                  className="bg-[#E8400C] text-white text-xs font-black py-3 px-4 rounded-[16px] hover:bg-[#D7380A] shadow-md shadow-[#E8400C]/15 transition-colors text-center w-full block mt-5"
                >
                  Open
                </Link>
              </div>
            ))}
          </div>
        </section>

      </main>

      {/* ── FOOTER ── */}
      <footer className="mt-10 border-t border-[#E2E8F0] bg-white px-6 py-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <Image src="/dau_logo.jpg" alt="DAU" width={120} height={30} className="h-7 w-auto object-contain opacity-60" />
          <p className="text-[11px] text-slate-400 text-center">
            © {new Date().getFullYear()} Dhirubhai Ambani University · Student Portal · Internal Use Only
          </p>
          <div className="flex items-center gap-4">
            <Link href="/student/academics" className="text-[11px] text-slate-400 hover:text-slate-700 transition-colors">Academics</Link>
            <Link href="/student/placements" className="text-[11px] text-slate-400 hover:text-slate-700 transition-colors">Placements</Link>
            <Link href="/student/chat" className="text-[11px] text-slate-400 hover:text-slate-700 transition-colors">AURA AI</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
