"use client";
import { useState } from "react";
import { Langue, TEXTES } from "../i18n";
import { Formulaire } from "../types";

export function FormulaireCitoyen({ initial, langue, consent }: { initial: Formulaire; langue: Langue; consent: boolean }) {
  const t = TEXTES[langue];
  const [champs, setChamps] = useState(initial.champs);
  const [lecture, setLecture] = useState(false);
  const [erreur, setErreur] = useState("");
  const [copie, setCopie] = useState(false);

  function modifier(nom: string, valeur: string) {
    setChamps((liste) => liste.map((c) => (c.nom === nom ? { ...c, valeur } : c)));
  }

  async function lirePiece(fichier: File) {
    setLecture(true);
    setErreur("");
    const donnees = new FormData();
    donnees.append("file", fichier);
    donnees.append("consentement", String(consent));
    donnees.append("procedure_id", initial.procedure_id);
    try {
      const reponse = await fetch("/api/upload", { method: "POST", body: donnees });
      const corps = await reponse.json();
      if (!reponse.ok) {
        setErreur(corps.detail || t.erreurService);
        return;
      }
      const detectes: Record<string, string> = corps.champs_detectes || {};
      setChamps((liste) => liste.map((c) => (detectes[c.nom] ? { ...c, valeur: detectes[c.nom] } : c)));
    } catch {
      setErreur(t.erreurConnexion);
    } finally {
      setLecture(false);
    }
  }

  async function copier() {
    const texte = champs.map((c) => `${t.champs[c.nom] || c.nom} : ${c.valeur}`).join("\n");
    await navigator.clipboard.writeText(texte);
    setCopie(true);
    setTimeout(() => setCopie(false), 1500);
  }

  return (
    <div className="max-w-[640px]">
      <p>{t.formulaireIntro(initial.plateforme)}</p>
      <p className="mt-3 border-l-[3px] border-[#c47f00] bg-attention-clair px-3 py-2 text-sm">{t.lectureAvertissement}</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {champs.map((c) => (
          <label key={c.nom} className="block text-sm font-semibold">
            {t.champs[c.nom] || c.nom}
            <input
              value={c.valeur}
              onChange={(e) => modifier(c.nom, e.target.value)}
              className="mt-1 block w-full rounded border border-ligne-forte bg-surface px-2.5 py-1.5 text-[15px] font-normal"
            />
          </label>
        ))}
      </div>
      {erreur && (
        <p role="alert" className="mt-3 border-l-[3px] border-erreur bg-erreur-clair px-3 py-2 text-sm text-erreur">
          {erreur}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <button onClick={copier} className="rounded bg-accent px-4 py-2 font-semibold text-white hover:bg-accent-fonce">
          {copie ? t.copie : t.copier}
        </button>
        <label className="cursor-pointer rounded border border-ligne-forte px-4 py-2 font-medium hover:bg-fond focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent">
          {lecture ? t.lecture : t.lirePiece}
          <input
            type="file"
            accept="image/png,image/jpeg"
            className="sr-only"
            disabled={lecture}
            onChange={(e) => {
              const fichier = e.target.files?.[0];
              if (fichier) lirePiece(fichier);
              e.target.value = "";
            }}
          />
        </label>
      </div>
    </div>
  );
}
