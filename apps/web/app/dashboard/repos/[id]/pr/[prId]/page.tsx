/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft, BrainCircuit, Clock, GitMerge } from "lucide-react";

export default async function PrPredictionPage({ params }: { params: Promise<{ id: string, prId: string }> }) {
  const resolvedParams = await params;
  const { id, prId } = resolvedParams;
  let prediction = null;
  let errorMsg = null;
  try {
    prediction = await ApiService.getPrediction(prId);
  } catch (err: any) {
    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
    console.error(err);
    errorMsg = err.message;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href={`/dashboard/repos/${id}`}><ArrowLeft className="h-5 w-5" /></Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">PR Intelligence</h1>
          <p className="text-muted-foreground mt-1">ML Merge Prediction</p>
        </div>
      </div>

      {errorMsg ? (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-6 text-destructive">
            Failed to load prediction: {errorMsg}
          </CardContent>
        </Card>
      ) : prediction ? (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><GitMerge className="h-5 w-5 text-primary" /> Merge Probability</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-6">
                <span className="text-6xl font-bold tracking-tighter text-primary">
                  {(prediction.mergeProbability * 100).toFixed(1)}%
                </span>
                <span className="text-muted-foreground mt-2 font-medium">Confidence: {(prediction.confidence * 100).toFixed(0)}%</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BrainCircuit className="h-5 w-5" /> Prediction Explanations</CardTitle>
              <CardDescription>Why the model made this prediction</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {prediction.reasons?.map((r: string, idx: number) => (
                  <li key={idx} className="flex items-center gap-2 bg-muted/50 p-2 rounded text-sm">
                    <span className="text-primary font-bold">+</span> {r.replace(/_/g, " ")}
                  </li>
                ))}
              </ul>
              <div className="mt-6 flex items-center gap-2 border-t pt-4">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Expected Time Bucket: <span className="text-primary">{prediction.mergeTimeBucket}</span></span>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="p-6">Loading...</div>
      )}
    </div>
  );
}
