/** Relaie une requête vers FastAPI en gardant un format d'erreur unique : { detail }. */
import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function relayer(chemin: string, init?: RequestInit): Promise<NextResponse> {
  try {
    const reponse = await fetch(`${API_URL}${chemin}`, { ...init, cache: "no-store" });
    const donnees = await reponse.json().catch(() => ({ detail: "Réponse illisible du service." }));
    return NextResponse.json(donnees, { status: reponse.status });
  } catch {
    return NextResponse.json(
      { detail: "Service indisponible. Vérifiez que le backend FastAPI est démarré." },
      { status: 503 },
    );
  }
}
