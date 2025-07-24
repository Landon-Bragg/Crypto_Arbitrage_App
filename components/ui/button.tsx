import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost"
  size?: "sm" | "lg"
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variant === "default" && "bg-purple-600 text-white hover:bg-purple-700",
        variant === "outline" && "border border-white/20 text-white bg-transparent hover:bg-white/10",
        variant === "ghost" && "bg-transparent text-white hover:bg-white/10",
        size === "sm" && "h-8 px-3 text-sm",
        size === "lg" && "h-12 px-6 text-lg",
        !size && "h-10 px-4 text-base",
        className
      )}
      {...props}
    />
  )
)
Button.displayName = "Button"