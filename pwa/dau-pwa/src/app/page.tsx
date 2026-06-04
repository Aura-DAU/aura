import Link from "next/link";
import Image from "next/image";

const features = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: "Academics",
    desc: "Courses, timetables, exam rules, academic calendar and faculty directory — all in one place.",
    href: "/student/academics",
    color: "from-blue-500/20 to-blue-600/5",
    accent: "#3B82F6",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0" />
      </svg>
    ),
    title: "Placements",
    desc: "Track upcoming drives, browse company profiles and access preparation material.",
    href: "/student/placements",
    color: "from-emerald-500/20 to-emerald-600/5",
    accent: "#10B981",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
      </svg>
    ),
    title: "Co-curricular",
    desc: "Discover student clubs, committees, and daily campus events.",
    href: "/student/cocurricular",
    color: "from-purple-500/20 to-purple-600/5",
    accent: "#A855F7",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
      </svg>
    ),
    title: "Career Horizons",
    desc: "Resources for GATE, CAT, UPSC, MS/PhD abroad, research and more.",
    href: "/student/career-horizons",
    color: "from-amber-500/20 to-amber-600/5",
    accent: "#F59E0B",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
      </svg>
    ),
    title: "Alumni Network",
    desc: "Connect with alumni, explore chapters and find mentorship opportunities.",
    href: "/student/alumni",
    color: "from-rose-500/20 to-rose-600/5",
    accent: "#F43F5E",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
      </svg>
    ),
    title: "AURA AI",
    desc: "Ask anything about campus life, policies, hostel rules, or clubs — instantly.",
    href: "/student/chat",
    color: "from-[#E8400C]/20 to-[#E8400C]/5",
    accent: "#E8400C",
  },
];

const stats = [
  { value: "25+", label: "Years of Excellence" },
  { value: "6000+", label: "Students Enrolled" },
  { value: "200+", label: "Recruiting Companies" },
  { value: "50+", label: "Student Clubs" },
];

export default function Home() {
  return (
    <>
      <style>{`
        @keyframes float-slow {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-30px) scale(1.05); }
        }
        @keyframes float-medium {
          0%, 100% { transform: translateY(0px) scale(1) rotate(0deg); }
          50% { transform: translateY(-20px) scale(1.03) rotate(3deg); }
        }
        @keyframes fade-up {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        @keyframes pulse-ring {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(232,64,12,0.4); }
          70% { transform: scale(1); box-shadow: 0 0 0 12px rgba(232,64,12,0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(232,64,12,0); }
        }
        .animate-float-slow { animation: float-slow 8s ease-in-out infinite; }
        .animate-float-medium { animation: float-medium 6s ease-in-out infinite; }
        .animate-fade-up { animation: fade-up 0.7s ease-out both; }
        .animate-fade-up-1 { animation: fade-up 0.7s 0.1s ease-out both; }
        .animate-fade-up-2 { animation: fade-up 0.7s 0.25s ease-out both; }
        .animate-fade-up-3 { animation: fade-up 0.7s 0.4s ease-out both; }
        .shimmer-text {
          background: linear-gradient(90deg, #fff 0%, #E8400C 40%, #fff 60%, #fff 100%);
          background-size: 200% auto;
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          animation: shimmer 4s linear infinite;
        }
        .card-hover {
          transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        }
        .card-hover:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .aura-pulse { animation: pulse-ring 2.5s ease-in-out infinite; }
      `}</style>

      <main className="min-h-screen bg-[#0A1628] text-white font-sans overflow-x-hidden">

        {/* ── NAV ── */}
        <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-4 bg-[#0A1628]/80 backdrop-blur-xl border-b border-white/5">
          <Image
            src="/dau_logo.jpg"
            alt="Dhirubhai Ambani University"
            width={160}
            height={40}
            priority
            className="h-9 w-auto object-contain brightness-110"
          />
          <div className="flex items-center gap-3">
            <Link
              href="/student/chat"
              className="hidden sm:flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white transition-colors px-4 py-2"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Ask AURA
            </Link>
            <Link
              href="/student/academics"
              className="text-xs font-bold bg-[#E8400C] hover:bg-[#D7380A] text-white px-5 py-2.5 rounded-full transition-all duration-200 shadow-lg shadow-[#E8400C]/25 hover:shadow-[#E8400C]/40"
            >
              Enter Portal →
            </Link>
          </div>
        </nav>

        {/* ── HERO ── */}
        <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-6 pt-24">

          {/* Background orbs */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="animate-float-slow absolute -top-20 -left-20 w-96 h-96 rounded-full bg-[#E8400C]/10 blur-3xl" />
            <div className="animate-float-medium absolute top-1/3 -right-32 w-80 h-80 rounded-full bg-blue-600/10 blur-3xl" />
            <div className="animate-float-slow absolute -bottom-20 left-1/3 w-72 h-72 rounded-full bg-purple-600/10 blur-3xl" style={{ animationDelay: "3s" }} />
            {/* Subtle grid */}
            <div
              className="absolute inset-0 opacity-[0.03]"
              style={{
                backgroundImage: `linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)`,
                backgroundSize: "60px 60px",
              }}
            />
          </div>

          <div className="relative z-10 max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="animate-fade-up inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 mb-8">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
                Student Portal · Dhirubhai Ambani University
              </span>
            </div>

            {/* Headline */}
            <h1 className="animate-fade-up-1 text-5xl md:text-7xl font-black leading-[1.05] tracking-tight mb-6">
              Your Campus.{" "}
              <span className="shimmer-text">One Portal.</span>
            </h1>

            {/* Subtext */}
            <p className="animate-fade-up-2 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed mb-10">
              Academics, placements, clubs, hostel rules, career resources — and an
              AI assistant that knows everything about campus life.
            </p>

            {/* CTAs */}
            <div className="animate-fade-up-3 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/student/academics"
                className="group flex items-center gap-2 bg-[#E8400C] hover:bg-[#D7380A] text-white font-bold text-sm px-8 py-4 rounded-full transition-all duration-200 shadow-xl shadow-[#E8400C]/30 hover:shadow-[#E8400C]/50 hover:scale-105"
              >
                Enter Student Portal
                <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </Link>
              <Link
                href="/student/chat"
                className="aura-pulse flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-[#E8400C]/40 text-white font-bold text-sm px-8 py-4 rounded-full transition-all duration-200"
              >
                <svg className="w-4 h-4 text-[#E8400C]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                Ask AURA AI
              </Link>
            </div>

            {/* Scroll indicator */}
            <div className="mt-16 flex flex-col items-center gap-1 text-slate-500 animate-bounce">
              <span className="text-[10px] uppercase tracking-widest font-semibold">Scroll to explore</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </section>

        {/* ── STATS ── */}
        <section className="border-y border-white/5 bg-white/[0.02] py-12 px-6">
          <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="text-3xl md:text-4xl font-black text-white mb-1">{s.value}</p>
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{s.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── FEATURES ── */}
        <section className="py-24 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <p className="text-xs font-black uppercase tracking-widest text-[#E8400C] mb-3">Everything in one place</p>
              <h2 className="text-3xl md:text-5xl font-black text-white leading-tight">
                Built for every aspect<br />of student life
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {features.map((f) => (
                <Link
                  key={f.title}
                  href={f.href}
                  className={`card-hover group relative bg-gradient-to-br ${f.color} border border-white/8 rounded-2xl p-6 overflow-hidden`}
                >
                  {/* Glow on hover */}
                  <div
                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl"
                    style={{ background: `radial-gradient(circle at 50% 0%, ${f.accent}18 0%, transparent 70%)` }}
                  />
                  <div className="relative z-10">
                    <div
                      className="inline-flex items-center justify-center w-11 h-11 rounded-xl mb-4"
                      style={{ backgroundColor: `${f.accent}20`, color: f.accent }}
                    >
                      {f.icon}
                    </div>
                    <h3 className="text-base font-black text-white mb-2">{f.title}</h3>
                    <p className="text-sm text-slate-400 leading-relaxed mb-4">{f.desc}</p>
                    <span
                      className="inline-flex items-center gap-1 text-xs font-bold group-hover:gap-2 transition-all duration-200"
                      style={{ color: f.accent }}
                    >
                      Explore
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                      </svg>
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* ── AURA HIGHLIGHT ── */}
        <section className="py-20 px-6">
          <div className="max-w-4xl mx-auto relative">
            <div className="relative overflow-hidden rounded-3xl border border-[#E8400C]/20 bg-gradient-to-br from-[#E8400C]/10 via-[#1a0a05] to-[#0A1628] p-10 md:p-14 text-center">
              {/* Orbs */}
              <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-[#E8400C]/15 blur-3xl pointer-events-none" />
              <div className="absolute -bottom-10 -left-10 w-48 h-48 rounded-full bg-[#E8400C]/10 blur-3xl pointer-events-none" />

              <div className="relative z-10">
                <div className="inline-flex items-center gap-2 bg-[#E8400C]/15 border border-[#E8400C]/30 rounded-full px-4 py-1.5 mb-6">
                  <span className="w-2 h-2 rounded-full bg-[#E8400C] animate-pulse" />
                  <span className="text-xs font-black uppercase tracking-widest text-[#E8400C]">AURA AI · Always Online</span>
                </div>
                <h2 className="text-3xl md:text-4xl font-black text-white mb-4 leading-tight">
                  Got a question about campus?
                </h2>
                <p className="text-slate-400 text-base md:text-lg leading-relaxed max-w-xl mx-auto mb-8">
                  AURA is your AI-powered campus assistant — trained on DAU policies, hostel rules,
                  academic guidelines, clubs and everything in between.
                </p>
                <Link
                  href="/student/chat"
                  className="inline-flex items-center gap-2 bg-[#E8400C] hover:bg-[#D7380A] text-white font-bold text-sm px-8 py-4 rounded-full transition-all duration-200 shadow-xl shadow-[#E8400C]/30 hover:shadow-[#E8400C]/50 hover:scale-105"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                  Start Chatting with AURA
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer className="border-t border-white/5 py-10 px-6">
          <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Image src="/dau_logo.jpg" alt="DAU" width={120} height={30} className="h-7 w-auto object-contain opacity-70" />
            </div>
            <p className="text-xs text-slate-500 text-center">
              © {new Date().getFullYear()} Dhirubhai Ambani University. Student Portal — Internal Use Only.
            </p>
            <div className="flex items-center gap-5">
              <Link href="/student/academics" className="text-xs text-slate-500 hover:text-white transition-colors">Academics</Link>
              <Link href="/student/placements" className="text-xs text-slate-500 hover:text-white transition-colors">Placements</Link>
              <Link href="/student/chat" className="text-xs text-slate-500 hover:text-white transition-colors">AURA AI</Link>
            </div>
          </div>
        </footer>

      </main>
    </>
  );
}
