"use client";
import { useMemo, useState } from "react";
import { DOMAINES_EN, Langue, TEXTES } from "../i18n";
import { DemarcheCatalogue, Statut } from "../types";
import { Etat } from "./icones";

const TONS: Record<Statut, "ok" | "attention" | "erreur"> = { couvert: "ok", partiel: "attention", lacune: "erreur" };
const TOUS = "__tous";
const LACUNES = "__lacunes";

export function Annuaire({ demarches, langue, onOuvrir }: { demarches: DemarcheCatalogue[]; langue: Langue; onOuvrir: (texte: string) => void }) {
  const t = TEXTES[langue];
  const [domaine, setDomaine] = useState(TOUS);
  const [filtre, setFiltre] = useState("");

  const nom = (d: DemarcheCatalogue) => (langue === "FR" ? d.nom : d.nom_en);
  const libelleDomaine = (d: string) => (langue === "FR" ? d : DOMAINES_EN[d] || d);

  const domaines = useMemo(() => {
    const compte = new Map<string, number>();
    demarches.forEach((d) => compte.set(d.domaine, (compte.get(d.domaine) || 0) + 1));
    return Array.from(compte.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "fr"));
  }, [demarches]);

  const lacunes = demarches.filter((d) => d.statut === "lacune").length;
  const couvertes = demarches.filter((d) => d.statut === "couvert").length;

  const normaliser = (texte: string) =>
    texte
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase();

  const affichees = demarches.filter((d) => {
    if (domaine === LACUNES && d.statut !== "lacune") return false;
    if (domaine !== TOUS && domaine !== LACUNES && d.domaine !== domaine) return false;
    return normaliser(nom(d)).includes(normaliser(filtre.trim()));
  });

  const choixDomaine = [
    { id: TOUS, libelle: t.tous, compte: demarches.length },
    ...domaines.map(([id, compte]) => ({ id, libelle: libelleDomaine(id), compte })),
    { id: LACUNES, libelle: t.lacunesFiltre, compte: lacunes },
  ];

  return (
    <div className="max-w-[1180px] px-4 py-6 lg:px-6">
      <h1 className="text-[26px] font-bold leading-tight">{t.annuaireTitre}</h1>
      {demarches.length > 0 && <p className="mt-1 text-texte-2">{t.annuaireResume(demarches.length, couvertes, lacunes)}</p>}

      <div className="mt-6 grid gap-6 lg:grid-cols-[250px_minmax(0,1fr)] lg:gap-8">
        <aside>
          <label className="block lg:hidden">
            <span className="mb-1 block text-sm font-semibold">{t.domaines}</span>
            <select
              value={domaine}
              onChange={(e) => setDomaine(e.target.value)}
              className="w-full rounded border border-ligne-forte bg-surface px-2.5 py-2"
            >
              {choixDomaine.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.libelle} ({c.compte})
                </option>
              ))}
            </select>
          </label>
          <div className="hidden lg:block">
            <h2 className="mb-1.5 text-sm font-semibold">{t.domaines}</h2>
            <ul>
              {choixDomaine.map((c) => (
                <li key={c.id} className={c.id === LACUNES ? "mt-2 border-t border-ligne pt-2" : ""}>
                  <button
                    onClick={() => setDomaine(c.id)}
                    aria-pressed={domaine === c.id}
                    className={`flex w-full items-baseline justify-between gap-2 border-l-[3px] px-2.5 py-1 text-left text-sm ${
                      domaine === c.id ? "border-accent bg-accent-clair font-semibold" : "border-transparent text-texte hover:bg-fond"
                    }`}
                  >
                    <span>{c.libelle}</span>
                    <span className="tabular-nums text-texte-2">{c.compte}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <section aria-label={t.annuaireTitre} className="min-w-0">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <label className="block w-full max-w-sm">
              <span className="mb-1 block text-sm font-semibold">{t.filtre}</span>
              <input
                type="search"
                value={filtre}
                onChange={(e) => setFiltre(e.target.value)}
                className="w-full rounded border border-ligne-forte bg-surface px-2.5 py-1.5"
              />
            </label>
            <p className="text-sm text-texte-2" aria-live="polite">
              {t.resultats(affichees.length)}
            </p>
          </div>

          <table className="mt-3 w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-texte text-sm">
                <th className="py-2 pr-4">{t.colonnes.demarche}</th>
                <th className="hidden py-2 pr-4 md:table-cell">{t.colonnes.administration}</th>
                <th className="py-2">{t.colonnes.etat}</th>
              </tr>
            </thead>
            <tbody>
              {affichees.map((d) => (
                <tr key={d.id} className="border-b border-ligne align-top hover:bg-fond">
                  <td className="py-2 pr-4">
                    <button onClick={() => onOuvrir(nom(d))} className="text-left font-medium text-accent underline-offset-2 hover:underline">
                      {nom(d)}
                    </button>
                    <span className="mt-0.5 block text-[13px] text-texte-2 md:hidden">{d.autorite}</span>
                  </td>
                  <td className="hidden py-2 pr-4 text-sm text-texte-2 md:table-cell">{d.autorite}</td>
                  <td className="py-2 text-sm">
                    <Etat ton={TONS[d.statut]}>{t.statuts[d.statut]}</Etat>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {affichees.length === 0 && demarches.length > 0 && <p className="mt-3 text-texte-2">{t.aucunResultat}</p>}

          <section className="mt-6 border-t border-ligne pt-3 text-sm" aria-label={t.legendeTitre}>
            <h2 className="font-semibold">{t.legendeTitre}</h2>
            <dl className="mt-1.5 space-y-1 text-texte-2">
              {(["couvert", "partiel", "lacune"] as Statut[]).map((s) => (
                <div key={s} className="sm:grid sm:grid-cols-[110px_minmax(0,1fr)]">
                  <dt className="font-medium text-texte">
                    <Etat ton={TONS[s]}>{t.statuts[s]}</Etat>
                  </dt>
                  <dd>{t.legende[s]}</dd>
                </div>
              ))}
            </dl>
          </section>
        </section>
      </div>
    </div>
  );
}
