import React from "react";
import { StudentProfile } from "@/lib/api/chat.action";

interface ProfileModalProps {
  show: boolean;
  profile: StudentProfile;
  onClose: () => void;
  onSave: (profile: StudentProfile) => void;
}

export default function ProfileModal({ show, profile, onClose, onSave }: ProfileModalProps) {
  const [formData, setFormData] = React.useState<StudentProfile>(profile);

  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFormData(profile);
  }, [profile]);

  if (!show) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full overflow-hidden shadow-2xl flex flex-col">
        <div className="p-6 border-b border-slate-800/80 flex justify-between items-center text-slate-100">
          <div>
            <h2 className="text-sm font-black leading-tight">Student Profile Settings</h2>
            <p className="text-[9px] text-slate-505 font-bold uppercase tracking-wide mt-0.5">Configure AURA Context</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">Student Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-primary-dau"
            />
          </div>
          <div className="grid grid-cols-2 gap-3.5">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">Academic Branch</label>
              <input
                type="text"
                value={formData.branch}
                onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-primary-dau"
              />
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">Semester</label>
              <input
                type="text"
                value={formData.semester}
                onChange={(e) => setFormData({ ...formData, semester: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-primary-dau"
              />
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">Special Interests / Tech</label>
            <input
              type="text"
              value={formData.interests}
              onChange={(e) => setFormData({ ...formData, interests: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-primary-dau"
            />
          </div>
          <div className="flex gap-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-slate-900 hover:bg-slate-850 text-slate-300 text-[10px] font-black uppercase py-3 rounded-xl border border-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-primary-dau hover:bg-[#D7380A] text-white text-[10px] font-black uppercase py-3 rounded-xl shadow transition-colors"
            >
              Save Context
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
