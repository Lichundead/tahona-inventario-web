import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"
import logo from "/assets/images/tahona-logo.webp"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

// Below 32px "Pastelería" stops being legible, so the kit asks for the name as text.
// shortcut: no symbol-only logo exists yet, use it here once the kit adds one
const LogoText = ({ className }: { className?: string }) => (
  <span className={cn("text-[10px] font-bold tracking-tight", className)}>
    Tahona
  </span>
)

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  // The cream outline separates the logo from both themes, so one image serves light and dark
  const fullLogo = (
    <img
      src={logo}
      alt="Tahona Pastelería"
      className={cn(
        "h-8 w-auto",
        variant === "responsive" && "group-data-[collapsible=icon]:hidden",
        className,
      )}
    />
  )

  const content =
    variant === "responsive" ? (
      <>
        {fullLogo}
        <LogoText className="hidden group-data-[collapsible=icon]:block" />
      </>
    ) : variant === "full" ? (
      fullLogo
    ) : (
      <LogoText className={className} />
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
