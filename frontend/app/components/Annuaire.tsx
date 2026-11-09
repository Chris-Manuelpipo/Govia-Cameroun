"use client";
import { useState } from "react";
import { DOMAINES_EN, Langue, TEXTES } from "../i18n";
import { DemarcheCatalogue, Statut } from "../types";
import { Etat, Icone, NomIcone } from "./icones";

/** Un état, une forme et une couleur : lisible sans la couleur. */
const STATUTS: Record<Statut, { ton: "ok" | "attention" | "erreur"; icone: NomIcone; couleur: string }> = {
  couvert: { ton: "ok", icone: "coche-cercle", couleur: "text-ok" },
  partiel: { ton: "attention", icone: "alerte", couleur: "text-attention-vif" },
  lacune: { ton: "erreur", icone: "document-barre", couleur: "text-erreur" },
};
const ORDRE: Statut[] = ["couvert", "partiel", "lacune"];
const GROUPE_FOND: Record<Statut, string> = {
  couvert: "bg-fond",
  partiel: "bg-attention-clair border-l-4 border-l-attention-vif",
  lacune: "bg-erreur-clair border-l-4 border-l-erreur",
};

type Filtre = "tous" | Statut;

const normaliser = (texte: string) =>
  texte
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();

export function Annuaire({
  demarches,
  erreur,
  langue,
  onOuvrir,
}: {
  demarches: DemarcheCatalogue[];
  erreur: boolean;
  langue: Langue;
  onOuvrir: (texte: string) => void;
}) {
  const t = TEXTES[langue];
  const [etat, setEtat] = useState<Filtre>("tous");
  const [domaine, setDomaine] = useState("");
  const [requete, setRequete] = useState("");

  const nom = (d: DemarcheCatalogue) => (langue === "FR" ? d.nom : d.nom_en);
  const libelleDomaine = (d: string) => (langue === "FR" ? d : DOMAINES_EN[d] || d);

  const compte = (statut: Statut) => demarches.filter((d) => d.statut === statut).length;
  const couvertes = compte("couvert");
  const partielles = compte("partiel");
  const lacunes = compte("lacune");

  const recherche = normaliser(requete.trim());
  const correspondRecherche = (d: DemarcheCatalogue) => !recherche || normaliser(`${nom(d)} ${d.autorite} ${libelleDomaine(d.domaine)}`).includes(recherche);
  const correspondEtat = (d: DemarcheCatalogue) => etat === "tous" || d.statut === etat;

  // Les effectifs du menu de domaines tiennent compte des autres filtres : ils annoncent ce qu'on obtiendra.
  const effectifs = new Map<string, number>();
  demarches.forEach((d) => {
    effectifs.set(d.domaine, (effectifs.get(d.domaine) || 0) + (correspondRecherche(d) && correspondEtat(d) ? 1 : 0));
  });
  const domaines = Array.from(effectifs.entries()).sort((a, b) => libelleDomaine(a[0]).localeCompare(libelleDomaine(b[0]), langue === "FR" ? "fr" : "en"));

  const visibles = demarches.filter((d) => correspondEtat(d) && correspondRecherche(d) && (!domaine || d.domaine === domaine));
  const totalDomaines = domaines.reduce((somme, [, n]) => somme + n, 0);

  const cartes: { id: Filtre; nombre: number; libelle: string }[] = [
    { id: "tous", nombre: demarches.length, libelle: t.etatsFiltre.tous },
    { id: "couvert", nombre: couvertes, libelle: t.etatsFiltre.couvert },
    { id: "partiel", nombre: partielles, libelle: t.etatsFiltre.partiel },
    { id: "lacune", nombre: lacunes, libelle: t.etatsFiltre.lacune },
  ];

  if (erreur && demarches.length === 0) {
    return (
      <div className="mx-auto max-w-[1280px] px-4 py-6 lg:px-6">
        <h1 className="text-[26px] font-bold leading-tight text-marine">{t.annuaireTitre}</h1>
        <p role="alert" className="mt-4 border-l-4 border-erreur bg-erreur-clair px-3 py-2 text-erreur">
          {t.annuaireIndisponible}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1280px] px-4 py-6 lg:px-6">
      <h1 className="text-[26px] font-bold leading-tight text-marine">{t.annuaireTitre}</h1>
      <p className="mt-1 max-w-[760px] text-texte-2">{t.annuaireIntro}</p>
      {demarches.length > 0 && <p className="mt-1 text-texte-2">{t.annuaireResume(demarches.length, couvertes, partielles, lacunes)}</p>}

      {/* Les lacunes sont une catégorie à part entière, au même rang que les démarches couvertes. */}
      <div role="group" aria-label={t.filtresEtat} className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {cartes.map((c) => {
          const actif = etat === c.id;
          const statut = c.id === "tous" ? null : c.id;
          return (
            <button
              key={c.id}
              onClick={() => setEtat(c.id)}
              aria-pressed={actif}
              className={`flex min-h-[76px] flex-col justify-between border border-t-4 px-4 py-2.5 text-left ${
                statut === "lacune" ? "border-t-erreur" : "border-t-transparent"
              } ${actif ? "border-marine bg-accent-clair outline outline-1 outline-marine" : "border-ligne bg-surface hover:border-ligne-forte"}`}
            >
              <span className="flex items-start justify-between gap-2">
                <span className="text-[26px] font-bold leading-none text-marine">{c.nombre}</span>
                {actif && <Icone nom="coche" taille={16} className="text-marine" />}
              </span>
              <span className="mt-1.5 flex items-center gap-1.5 text-[14px] leading-tight">
                {statut && <Icone nom={STATUTS[statut].icone} taille={15} className={STATUTS[statut].couleur} />}
                {c.libelle}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(220px,300px)]">
        <label className="block">
          <span className="mb-1 block text-sm font-semibold">{t.rechercher}</span>
          <span className="relative block">
            <Icone nom="loupe" taille={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-texte-2" />
            <input
              type="search"
              value={requete}
              onChange={(e) => setRequete(e.target.value)}
              placeholder={t.recherchePlaceholder}
              className="h-11 w-full border border-ligne-forte bg-surface pl-10 pr-3 placeholder:text-texte-2"
            />
          </span>
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-semibold">{t.domaine}</span>
          <select value={domaine} onChange={(e) => setDomaine(e.target.value)} className="h-11 w-full border border-ligne-forte bg-surface px-2.5">
            <option value="">
              {t.tousDomaines} ({totalDomaines})
            </option>
            {domaines.map(([id, effectif]) => (
              <option key={id} value={id}>
                {libelleDomaine(id)} ({effectif})
              </option>
            ))}
          </select>
        </label>
      </div>

      <p className="mt-4 text-sm text-texte-2" aria-live="polite">
        {t.resultats(visibles.length)}
      </p>

      <div className="mt-1 overflow-x-auto border border-ligne bg-surface">
        <table className="w-full border-collapse">
          <caption className="sr-only">{t.annuaireTitre}</caption>
          <thead>
            <tr className="border-b-2 border-marine text-sm">
              <th scope="col" className="px-3 py-2.5">
                {t.colonnes.demarche}
              </th>
              <th scope="col" className="hidden px-3 py-2.5 lg:table-cell">
                {t.colonnes.domaine}
              </th>
              <th scope="col" className="hidden px-3 py-2.5 md:table-cell">
                {t.colonnes.administration}
              </th>
              <th scope="col" className="px-3 py-2.5">
                {t.colonnes.etat}
              </th>
            </tr>
          </thead>
          {ORDRE.map((statut) => {
            const lignes = visibles.filter((d) => d.statut === statut);
            if (!lignes.length) return null;
            return (
              <tbody key={statut}>
                <tr>
                  <th colSpan={4} scope="rowgroup" className={`border-b border-ligne px-3 py-2 text-[14px] ${GROUPE_FOND[statut]}`}>
                    <span className="flex items-center gap-2">
                      <Icone nom={STATUTS[statut].icone} taille={16} className={STATUTS[statut].couleur} />
                      {t.groupes[statut](lignes.length)}
                    </span>
                    {statut === "lacune" && <span className="mt-0.5 block text-[13px] font-normal text-texte-2">{t.groupeLacune}</span>}
                  </th>
                </tr>
                {lignes.map((d) => (
                  <tr key={d.id} data-demarche={d.id} className="border-b border-ligne align-middle last:border-b-0 hover:bg-fond">
                    <td className="px-3">
                      <button onClick={() => onOuvrir(nom(d))} className="min-h-[44px] w-full py-2 text-left font-medium text-accent underline-offset-2 hover:underline">
                        {nom(d)}
                      </button>
                      <span className="-mt-1 block pb-2 text-[13px] text-texte-2 md:hidden">{d.autorite}</span>
                    </td>
                    <td className="hidden px-3 py-2 text-sm text-texte-2 lg:table-cell">{libelleDomaine(d.domaine)}</td>
                    <td className="hidden px-3 py-2 text-sm text-texte-2 md:table-cell">{d.autorite}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-sm">
                      <Etat ton={STATUTS[d.statut].ton} icone={STATUTS[d.statut].icone}>
                        {t.statuts[d.statut]}
                      </Etat>
                    </td>
                  </tr>
                ))}
              </tbody>
            );
          })}
        </table>
        {visibles.length === 0 && demarches.length > 0 && <p className="px-3 py-4 text-texte-2">{t.aucunResultat}</p>}
      </div>

      <section className="mt-6 border-t border-ligne pt-3 text-sm" aria-label={t.legendeTitre}>
        <h2 className="font-semibold">{t.legendeTitre}</h2>
        <dl className="mt-1.5 space-y-1 text-texte-2">
          {ORDRE.map((s) => (
            <div key={s} className="sm:grid sm:grid-cols-[170px_minmax(0,1fr)]">
              <dt className="font-medium text-texte">
                <Etat ton={STATUTS[s].ton} icone={STATUTS[s].icone}>
                  {t.statuts[s]}
                </Etat>
              </dt>
              <dd>{t.legende[s]}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
