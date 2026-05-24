import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "group relative inline-flex min-h-11 items-center justify-center gap-2 overflow-hidden whitespace-nowrap rounded-2xl text-sm font-semibold transition duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-civic-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-civic-bg disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-white text-civic-bg shadow-[0_16px_45px_rgba(255,255,255,0.16)] before:absolute before:inset-0 before:bg-[linear-gradient(110deg,transparent,rgba(79,140,255,0.24),transparent)] before:translate-x-[-120%] hover:before:translate-x-[120%] before:transition-transform before:duration-700 hover:bg-slate-100 active:scale-[0.98]",
        secondary:
          "border border-white/12 bg-white/10 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] backdrop-blur-xl hover:border-civic-cyan/30 hover:bg-white/15 hover:shadow-glow active:scale-[0.98]",
        ghost:
          "text-slate-300 hover:bg-white/10 hover:text-white active:scale-[0.98]",
        gradient:
          "bg-gradient-to-r from-civic-blue via-civic-purple to-civic-cyan text-white shadow-[0_18px_50px_rgba(0,212,255,0.22)] before:absolute before:inset-0 before:bg-[linear-gradient(110deg,transparent,rgba(255,255,255,0.28),transparent)] before:translate-x-[-120%] hover:before:translate-x-[120%] before:transition-transform before:duration-700 hover:brightness-110 active:scale-[0.98]",
        outline:
          "border border-civic-cyan/30 bg-civic-cyan/8 text-civic-cyan shadow-[inset_0_1px_0_rgba(255,255,255,0.10)] hover:bg-civic-cyan/14 hover:shadow-glow active:scale-[0.98]"
      },
      size: {
        default: "h-12 px-5 py-3",
        sm: "h-10 rounded-xl px-4 text-xs",
        lg: "h-14 rounded-2xl px-6 text-base",
        icon: "size-11 rounded-2xl p-0"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
