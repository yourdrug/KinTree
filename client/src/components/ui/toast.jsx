import * as React from "react";
import * as ToastPrimitives from "@radix-ui/react-toast";
import { cva } from "class-variance-authority";
import { X, CheckCircle2, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Provider & Viewport ───────────────────────────────────────────────────────

const ToastProvider = ToastPrimitives.Provider;

const ToastViewport = React.forwardRef(({ className, ...props }, ref) => (
  <ToastPrimitives.Viewport
    ref={ref}
    className={cn(
      "fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm outline-none",
      className
    )}
    {...props}
  />
));
ToastViewport.displayName = ToastPrimitives.Viewport.displayName;

// ── Toast variants ────────────────────────────────────────────────────────────

const toastVariants = cva(
  [
    "group relative flex w-full items-start gap-3 overflow-hidden rounded-2xl border p-4 shadow-lg",
    "data-[state=open]:animate-in data-[state=open]:slide-in-from-right-full data-[state=open]:fade-in-0 data-[state=open]:duration-300",
    "data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right-full data-[state=closed]:fade-out-0 data-[state=closed]:duration-200",
    "data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)]",
    "data-[swipe=cancel]:translate-x-0 data-[swipe=cancel]:transition-transform",
    "data-[swipe=end]:slide-out-to-right-full data-[swipe=end]:animate-out",
  ].join(" "),
  {
    variants: {
      variant: {
        default:     "bg-white border-border",
        destructive: "bg-white border-red-100",
        success:     "bg-white border-green-100",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

// ── Progress bar (визуальный таймер) ─────────────────────────────────────────

function ToastProgress({ variant, duration = 4000 }) {
  const color =
    variant === "destructive" ? "bg-red-400" :
    variant === "success"     ? "bg-green-500" :
    "bg-primary";

  return (
    <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-muted overflow-hidden rounded-b-2xl">
      <div
        className={cn("h-full origin-left", color)}
        style={{
          animation: `toast-progress ${duration}ms linear forwards`,
        }}
      />
      <style>{`
        @keyframes toast-progress {
          from { transform: scaleX(1); }
          to   { transform: scaleX(0); }
        }
      `}</style>
    </div>
  );
}

// ── Toast root ────────────────────────────────────────────────────────────────

const Toast = React.forwardRef(({ className, variant, duration, children, ...props }, ref) => (
  <ToastPrimitives.Root
    ref={ref}
    className={cn(toastVariants({ variant }), className)}
    {...props}
  >
    {children}
    <ToastProgress variant={variant} duration={duration} />
  </ToastPrimitives.Root>
));
Toast.displayName = ToastPrimitives.Root.displayName;

// ── Icon по варианту ──────────────────────────────────────────────────────────

function ToastIcon({ variant }) {
  if (variant === "destructive")
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center bg-red-50">
        <AlertCircle className="w-4 h-4 text-red-500" />
      </div>
    );
  if (variant === "success")
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center bg-green-50">
        <CheckCircle2 className="w-4 h-4 text-green-600" />
      </div>
    );
  return (
    <div
      className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center"
      style={{ background: "hsl(145,35%,94%)" }}
    >
      <Info className="w-4 h-4" style={{ color: "hsl(145,35%,38%)" }} />
    </div>
  );
}

// ── Close button ──────────────────────────────────────────────────────────────

const ToastClose = React.forwardRef(({ className, ...props }, ref) => (
  <ToastPrimitives.Close
    ref={ref}
    toast-close=""
    className={cn(
      "absolute right-3 top-3 rounded-lg p-1",
      "opacity-0 group-hover:opacity-100 transition-opacity",
      "hover:bg-muted focus:opacity-100 focus:outline-none",
      className
    )}
    {...props}
  >
    <X className="w-3.5 h-3.5 text-muted-foreground" />
  </ToastPrimitives.Close>
));
ToastClose.displayName = ToastPrimitives.Close.displayName;

// ── Title & Description ───────────────────────────────────────────────────────

const ToastTitle = React.forwardRef(({ className, ...props }, ref) => (
  <ToastPrimitives.Title
    ref={ref}
    className={cn("text-sm font-semibold leading-tight text-foreground", className)}
    {...props}
  />
));
ToastTitle.displayName = ToastPrimitives.Title.displayName;

const ToastDescription = React.forwardRef(({ className, ...props }, ref) => (
  <ToastPrimitives.Description
    ref={ref}
    className={cn("text-xs text-muted-foreground mt-0.5 leading-relaxed", className)}
    {...props}
  />
));
ToastDescription.displayName = ToastPrimitives.Description.displayName;

const ToastAction = React.forwardRef(({ className, ...props }, ref) => (
  <ToastPrimitives.Action
    ref={ref}
    className={cn(
      "inline-flex h-8 shrink-0 items-center justify-center rounded-lg border px-3",
      "text-xs font-medium transition-colors hover:bg-muted",
      "focus:outline-none focus:ring-1 focus:ring-ring",
      className
    )}
    {...props}
  />
));
ToastAction.displayName = ToastPrimitives.Action.displayName;

export {
  ToastProvider,
  ToastViewport,
  Toast,
  ToastIcon,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastAction,
};
