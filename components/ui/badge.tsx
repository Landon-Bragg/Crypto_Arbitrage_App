import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary"
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-colors",
        variant === "default"
          ? "bg-purple-600 text-purple-100 border border-purple-600/30"
          : "bg-white/10 text-purple-300 border border-white/20",
        className
      )}
      {...props}
    />
  )
}