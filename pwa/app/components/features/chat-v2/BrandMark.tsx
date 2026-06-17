import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface BrandMarkProps {
  size?: "sm" | "md";
  className?: string;
}

export default function BrandMark({ size = "md", className }: BrandMarkProps) {
  const dim = size === "sm" ? "h-7 w-7" : "h-8 w-8";
  const icon = size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4";
  return (
    <div
      className={cn(
        "rounded-full bg-gradient-to-br from-theme-red to-theme-yellow p-[1.5px] shrink-0",
        dim,
        className,
      )}
    >
      <div className="grid h-full w-full place-items-center rounded-full bg-theme-black">
        <Sparkles className={cn("text-theme-yellow", icon)} strokeWidth={2.25} />
      </div>
    </div>
  );
}
