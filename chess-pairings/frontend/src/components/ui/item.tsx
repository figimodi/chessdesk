import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ItemProps = HTMLAttributes<HTMLDivElement> & {
  variant?: "outline";
  size?: "sm";
};

export const Item = forwardRef<HTMLDivElement, ItemProps>(function Item({ className, variant, size, ...props }, ref) {
  return <div ref={ref} className={cn("flex items-center justify-between gap-3 rounded-xl border bg-white px-3 py-2 text-sm", variant === "outline" ? "border" : "", size === "sm" ? "py-2" : "", className)} {...props} />;
});

export const ItemContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function ItemContent({ className, ...props }, ref) {
  return <div ref={ref} className={cn("min-w-0 flex-1", className)} {...props} />;
});

export const ItemTitle = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function ItemTitle({ className, ...props }, ref) {
  return <div ref={ref} className={cn("truncate font-medium", className)} {...props} />;
});

export const ItemActions = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function ItemActions({ className, ...props }, ref) {
  return <div ref={ref} className={cn("flex items-center gap-2", className)} {...props} />;
});
