import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AlertCard({
  message,
  title = "Errore",
  onClose,
}: {
  message: string;
  title?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const timeout = window.setTimeout(onClose, 5000);
    return () => window.clearTimeout(timeout);
  }, [onClose]);

  return (
    <div className="fixed right-4 top-4 z-50 w-full max-w-sm">
      <Card className="border-red-300 bg-red-100 shadow-lg">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-base text-red-900">{title}</CardTitle>
          </div>
          <Button className="h-7 px-2 text-red-900 hover:bg-red-200" variant="ghost" size="sm" onClick={onClose}>Chiudi</Button>
        </CardHeader>
        <CardContent className="pt-0 text-sm text-red-800">{message}</CardContent>
      </Card>
    </div>
  );
}
