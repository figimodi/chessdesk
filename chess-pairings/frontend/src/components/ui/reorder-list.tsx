"use client";

import React, { Children, isValidElement, useEffect, useMemo, useState } from "react";
import { Grip } from "lucide-react";
import { cn } from "@/lib/utils";

type ReorderListEntry = {
  id: string;
  element: React.ReactElement;
};

export interface ReorderListProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactElement[] | React.ReactElement;
  className?: string;
  itemClassName?: string;
  draggable?: boolean;
  withDragHandle?: boolean;
  onReorderFinish?: (newOrder: React.ReactElement[], orderIds: string[]) => void;
}

export function ReorderList({
  className,
  itemClassName,
  draggable = true,
  withDragHandle = false,
  onReorderFinish,
  children,
  ...props
}: ReorderListProps) {
  const normalizedChildren = useMemo(() => {
    return Children.toArray(children)
      .filter((child): child is React.ReactElement => isValidElement(child))
      .map((child, index) => ({
        id: normalizeReactKey(child.key, index),
        element: child,
      }));
  }, [children]);
  const childrenSignature = useMemo(() => normalizedChildren.map((child) => child.id).join("|"), [normalizedChildren]);
  const [items, setItems] = useState<ReorderListEntry[]>(normalizedChildren);
  const [draggedId, setDraggedId] = useState<string | null>(null);

  useEffect(() => {
    setItems(normalizedChildren);
  }, [childrenSignature, normalizedChildren]);

  const finishReorder = (nextItems: ReorderListEntry[]) => {
    setItems(nextItems);
    onReorderFinish?.(
      nextItems.map((item) => item.element),
      nextItems.map((item) => item.id),
    );
  };

  const reorderByTarget = (targetId: string) => {
    if (!draggedId || draggedId === targetId) return;

    const fromIndex = items.findIndex((item) => item.id === draggedId);
    const toIndex = items.findIndex((item) => item.id === targetId);
    if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex) return;

    const reordered = [...items];
    const [moved] = reordered.splice(fromIndex, 1);
    reordered.splice(toIndex, 0, moved);
    finishReorder(reordered);
  };

  return (
    <div data-slot="reorder-list-group" className={cn("flex list-none flex-col gap-1 select-none !m-0 !p-0", className)} {...props}>
      {items.map((item, index) => (
        <ReorderListItem
          key={item.id || index}
          className={itemClassName}
          draggable={draggable}
          draggedId={draggedId}
          item={item}
          withDragHandle={withDragHandle}
          onDragEnd={() => setDraggedId(null)}
          onDragStart={(id) => setDraggedId(id)}
          onDropOnItem={(id) => {
            reorderByTarget(id);
            setDraggedId(null);
          }}
        />
      ))}
    </div>
  );
}

function ReorderListItem({
  item,
  className,
  draggable = true,
  withDragHandle = false,
  draggedId,
  onDragStart,
  onDragEnd,
  onDropOnItem,
}: {
  item: ReorderListEntry;
  className?: string;
  draggable?: boolean;
  withDragHandle?: boolean;
  draggedId: string | null;
  onDragStart: (id: string) => void;
  onDragEnd: () => void;
  onDropOnItem: (id: string) => void;
}) {
  const isDragging = draggedId === item.id;

  return (
    <div
      data-slot="reorder-list-item"
      className={cn("list-none !m-0 !p-0 bg-background", draggable && !withDragHandle ? "cursor-grab" : "", isDragging ? "opacity-60" : "", className)}
      draggable={draggable && !withDragHandle}
      onDragStart={() => onDragStart(item.id)}
      onDragEnd={onDragEnd}
      onDragOver={(event) => {
        if (!draggable) return;
        event.preventDefault();
      }}
      onDrop={() => {
        if (!draggable) return;
        onDropOnItem(item.id);
      }}
    >
      {withDragHandle ? (
        <div className="relative flex items-center gap-2">
          {isValidElement<{ className?: string }>(item.element)
            ? React.cloneElement(item.element, {
                className: cn("w-full pr-12", item.element.props.className),
              })
            : item.element}
          <div
            className="absolute right-4 top-1/2 -translate-y-1/2 cursor-grab text-muted-foreground"
            draggable={draggable}
            onDragStart={() => onDragStart(item.id)}
            onDragEnd={onDragEnd}
          >
            <Grip className="size-6" />
          </div>
        </div>
      ) : (
        item.element
      )}
    </div>
  );
}

function normalizeReactKey(key: React.Key | null, index: number) {
  if (key == null) return String(index);

  return String(key)
    .replace(/^\.\$/, "")
    .replace(/^\./, "")
    .replace(/=0/g, "=")
    .replace(/=2/g, ":");
}
