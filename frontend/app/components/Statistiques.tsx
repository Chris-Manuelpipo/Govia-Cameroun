"use client";
import { Textes } from "../i18n";
import { DocumentSource, Stats } from "../types";
import { Etat } from "./icones";

export interface Chiffres {
  documents: number;
  extraits: number;
  verifies: number;
  aVerifier: number;
}

/** Chiffres de l'API ; à défaut, recalculés depuis la liste des documents (chaque document est vérifié en entier ou pas du tout). */
export function chiffres(stats: Stats | null, documents: DocumentSource[]): Chiffres | null {
  if (stats) {
    return {
      documents: stats.total_documents,
      extraits: stats.total_chunks,
      verifies: stats.par_statut_verification.verifie || 0,
      aVerifier: stats.par_statut_verification.a_verifier || 0,
    };
  }
  if (!documents.length) return null;
  const extraits = documents.reduce((total, d) => total + d.chunks, 0);
  const aVerifier = documents.filter((d) => d.statut_verification !== "verifie").reduce((total, d) => total + d.chunks, 0);
  return { documents: documents.length, extraits, verifies: extraits - aVerifier, aVerifier };
}

function Tuile({ libelle, valeur, repere }: { libelle: string; valeur: number; repere?: React.ReactNode }) {
  return (
    <div className="flex flex-col-reverse justify-end border border-ligne bg-surface px-4 py-3">
      <dt className="mt-1.5 text-[13px] leading-snug text-texte-2">{repere || libelle}</dt>
      <dd className="text-[30px] font-semibold leading-none text-titre">{valeur}</dd>
    </div>
  );
}

/**
 * Rangée de tuiles (un chiffre, un libellé) et jauge fine : la part des extraits relus à la source.
 * Deux segments séparés de 2 px, bouts arrondis ; les nombres sont écrits à côté, la jauge n'est qu'un repère.
 */
export function Statistiques({ chiffres: c, t, compact = false }: { chiffres: Chiffres; t: Textes; compact?: boolean }) {
  const pourcent = c.extraits ? Math.round((c.verifies / c.extraits) * 100) : 0;
  return (
    <div>
      <dl className={`grid gap-3 ${compact ? "grid-cols-2" : "grid-cols-2 lg:grid-cols-4"}`}>
        <Tuile libelle={t.statDocuments} valeur={c.documents} />
        <Tuile libelle={t.statExtraits} valeur={c.extraits} />
        <Tuile libelle={t.statVerifies} valeur={c.verifies} repere={<Etat ton="ok">{t.statVerifies}</Etat>} />
        <Tuile libelle={t.statAVerifier} valeur={c.aVerifier} repere={<Etat ton="attention">{t.statAVerifier}</Etat>} />
      </dl>

      <div className="mt-4">
        <div role="img" aria-label={t.jaugeNom(c.verifies, c.extraits, c.aVerifier)} className="flex h-2 gap-0.5">
          <span style={{ flexGrow: c.verifies }} className="basis-0 rounded-full bg-ok" />
          {c.aVerifier > 0 && <span style={{ flexGrow: c.aVerifier }} className="min-w-[6px] basis-0 rounded-full bg-attention-vif" />}
        </div>
        <p className="mt-1.5 text-[13px] text-texte-2">{t.partVerifiee(pourcent)}</p>
      </div>
    </div>
  );
}
