import React from "react";
import { StudentProfile } from "@/app/api/chat.service";
import { UserSession } from "@/hooks/use-aura-chat";

interface ProfileModalProps {
  show: boolean;
  profile: StudentProfile;
  onClose: () => void;
  onSave: (profile: StudentProfile) => void;
  userSession?: UserSession | null;
}

const inputClass =
  "w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 hover:border-slate-400 rounded-md px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-100 disabled:opacity-75 disabled:cursor-not-allowed";

const labelClass = "block text-[13px] font-medium text-slate-600 dark:text-slate-400 mb-1";

export default function ProfileModal({
  show,
  profile,
  onClose,
  onSave,
  userSession
}: ProfileModalProps) {
  const [formData, setFormData] = React.useState<StudentProfile>(profile);
  const dialogRef = React.useRef<HTMLDivElement | null>(null);

  const isParent = userSession?.role === "parent";

  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFormData(profile);
  }, [profile]);

  // Focus trap: move focus into the dialog on open, cycle Tab/Shift+Tab
  // within it, and close on Escape.
  React.useEffect(() => {
    if (!show) return;

    const dialog = dialogRef.current;
    const focusable = dialog?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    focusable?.[0]?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !focusable || focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [show, onClose]);

  if (!show) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isParent) return;
    onSave(formData);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Student profile settings"
    >
      <div
        ref={dialogRef}
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full overflow-hidden shadow-2xl flex flex-col animate-in fade-in zoom-in-95 duration-200"
      >
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center text-slate-900 dark:text-slate-100">
          <div>
            <h2 className="text-sm font-semibold leading-tight">
              {isParent ? "Linked Student Profile" : "Student Profile Settings"}
            </h2>
            <p className="text-[12px] text-slate-500 mt-0.5">
              {isParent
                ? "Read-only view of your child's profile used to personalize AURA"
                : "Used to personalize AURA's answers"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors hover:cursor-pointer"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className={labelClass}>Student Name</label>
            <input
              type="text"
              disabled={isParent}
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className={inputClass}
            />
          </div>
          <div className="grid grid-cols-2 gap-3.5">
            <div>
              <label className={labelClass}>Academic Branch</label>
              <input
                type="text"
                disabled={isParent}
                value={formData.branch}
                onChange={(e) =>
                  setFormData({ ...formData, branch: e.target.value })
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Semester</label>
              <input
                type="text"
                disabled={isParent}
                value={formData.semester}
                onChange={(e) =>
                  setFormData({ ...formData, semester: e.target.value })
                }
                className={inputClass}
              />
            </div>
          </div>
          <div>
            <label className={labelClass}>Interests / Focus Area</label>
            <input
              type="text"
              disabled={isParent}
              value={formData.interests}
              onChange={(e) =>
                setFormData({ ...formData, interests: e.target.value })
              }
              className={inputClass}
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-white hover:bg-slate-50 dark:bg-transparent dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-medium py-2.5 rounded-md border border-slate-300 dark:border-slate-800 transition-colors hover:cursor-pointer"
            >
              {isParent ? "Close" : "Cancel"}
            </button>
            {!isParent && (
              <button
                type="submit"
                className="flex-1 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium py-2.5 rounded-md transition-colors hover:cursor-pointer"
              >
                Save
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
