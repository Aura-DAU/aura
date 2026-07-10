import { WifiOff } from "lucide-react"
import { BrandMark } from "@/components/common/BrandMark"

export default function OfflinePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <BrandMark />
      <div className="flex flex-col items-center gap-2">
        <WifiOff className="h-10 w-10 text-muted-foreground" />
        <h1 className="text-xl font-semibold">You're offline</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          AURA needs a connection to answer questions and fetch your ERP data.
          Reconnect and try again — anything you'd already loaded this session
          (like fee status or your timetable) may still be visible from cache.
        </p>
      </div>
    </div>
  )
}
