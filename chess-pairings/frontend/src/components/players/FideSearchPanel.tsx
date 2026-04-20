import { useState } from "react";
import { Search, Upload } from "lucide-react";
import { useFideSearch, useImportPlayerFromFide } from "@/api/hooks/players";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function FideSearchPanel() {
  const [query, setQuery] = useState("");
  const { data, isFetching } = useFideSearch(query);
  const importMutation = useImportPlayerFromFide();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Catalogo giocatori</CardTitle>
        <CardDescription>Search players in FIDE database and import the selected player.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3.5 h-4 w-4 text-[var(--muted-foreground)]" />
            <Input className="pl-9" placeholder="Search player name or ID" value={query} onChange={(event) => setQuery(event.target.value)} />
          </div>
          <Button variant="secondary" disabled={isFetching}>
            {isFetching ? "Searching..." : "Refresh"}
          </Button>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>FIDE ID</TableHead>
                <TableHead>Federation</TableHead>
                <TableHead>Standard</TableHead>
                <TableHead>Rapid</TableHead>
                <TableHead>Blitz</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data ?? []).map((player) => (
                <TableRow key={player.fide_id}>
                  <TableCell className="min-w-56">{player.full_name}</TableCell>
                  <TableCell className="min-w-28">{player.fide_id}</TableCell>
                  <TableCell>{player.federation ?? "-"}</TableCell>
                  <TableCell>{player.standard_rating ?? player.rating ?? "-"}</TableCell>
                  <TableCell>{player.rapid_rating ?? "-"}</TableCell>
                  <TableCell>{player.blitz_rating ?? "-"}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm" onClick={() => importMutation.mutate(player.fide_id)}>
                      <Upload className="h-4 w-4" />
                      Import
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
