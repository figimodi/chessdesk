import { Link } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function NotFoundPage() {
  return (
    <AppShell>
      <Card>
        <CardHeader>
          <CardTitle>Pagina non trovata</CardTitle>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link to="/">Torna alla dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </AppShell>
  );
}
