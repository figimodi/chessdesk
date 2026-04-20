import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-[var(--primary)] px-4 py-2 text-[var(--primary-foreground)] shadow-sm hover:opacity-90",
        secondary: "bg-[var(--muted)] px-4 py-2 text-[var(--foreground)] hover:bg-white",
        outline: "border bg-white px-4 py-2 hover:bg-[var(--muted)]",
        ghost: "px-4 py-2 hover:bg-[var(--muted)]",
        destructive: "bg-red-600 px-4 py-2 text-white shadow-sm hover:bg-red-700",
      },
      size: {
        default: "h-10",
        sm: "h-9 px-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);

Button.displayName = "Button";
