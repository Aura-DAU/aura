import { toast } from "sonner"

export function toastError(message: string): void {
  toast.error(message)
}

export function toastSuccess(message: string): void {
  toast.success(message)
}

export function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message.trim()) return err.message
  if (typeof err === "string" && err.trim()) return err
  return fallback
}
