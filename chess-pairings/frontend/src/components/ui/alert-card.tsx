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
  return (
    <div className="fixed right-4 top-4 z-50 w-full max-w-md">
      <Card className="border-red-200 bg-red-50">
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-red-800">{title}</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>Chiudi</Button>
        </CardHeader>
        <CardContent className="text-sm text-red-700">{message}</CardContent>
      </Card>
    </div>
  );
}
