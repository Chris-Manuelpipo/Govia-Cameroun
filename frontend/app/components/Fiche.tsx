"use client";
import { useMemo, useState } from "react";
import { analyser, Analyse, grouper, Section, separerExtrait } from "../lib/reponse";
import { Langue, TEXTES, Textes } from "../i18n";
import { Audit, Citation, Message } from "../types";
import { FormulaireCitoyen } from "./Formulaire";
import { Etat, Icone } from "./icones";

/** Affiche le gras produit par l'agent, sans jamais injecter de HTML. */
function Riche({ texte }: { texte: string }) {
  return (
    <>
      {texte.split(/(\*\*[^*]+\*\*)/g).map((m, i) =>
        m.startsWith("**") && m.endsWith("**") ? <strong key={i}>{m.slice(2, -2)}</strong> : <span key={i}>{m}</span>,
      )}
    </>
  );
}

function Titre2({ children, droite }: { children: React.ReactNode; droite?: React.ReactNode }) {
  return (
    <div className="mb-1 flex flex-wrap items-baseline justify-between gap-x-3 border-b-2 border-texte pb-1.5">
      <h2 className="text-[17px] font-bold">{children}</h2>
      {droite && <span className="text-sm text-texte-2">{droite}</span>}
    </div>
  );
}

function Pieces({ section, t }: { section: Section; t: Textes }) {
  const [cochees, setCochees] = useState<Set<number>>(new Set());
  const groupes = useMemo(() => grouper(section.items), [section.items]);

  function basculer(position: number) {
    setCochees((actuelles) => {
      const suivantes = new Set(actuelles);
      if (suivantes.has(position)) suivantes.delete(position);
      else suivantes.add(position);
      return suivantes;
    });
  }

  let debut = 0;
  return (
    <section>
      <Titre2 droite={t.piecesPretes(cochees.size, section.items.length)}>{section.titre}</Titre2>
      {groupes.map((groupe, g) => {
        const depart = debut;
        debut += groupe.items.length;
        return (
          <div key={g}>
            {groupe.nom && <h3 className="mt-3 text-[15px] font-semibold">{groupe.nom}</h3>}
            <ul className="divide-y divide-ligne">
              {groupe.items.map((item, i) => {
                const position = depart + i;
                const cochee = cochees.has(position);
                return (
                  <li key={position}>
                    <label className="flex cursor-pointer items-start gap-2.5 py-2 hover:bg-fond">
                      <input type="checkbox" checked={cochee} onChange={() => basculer(position)} className="mt-[3px] h-4 w-4 shrink-0 accent-[#0b5cad]" />
                      <span className={`extrait-exact block ${cochee ? "text-texte-2 line-through" : ""}`}>{item}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </section>
  );
}

function Etapes({ section }: { section: Section }) {
  const groupes = useMemo(() => grouper(section.items), [section.items]);
  let debut = 0;
  return (
    <section>
      <Titre2>{section.titre}</Titre2>
      {groupes.map((groupe, g) => {
        const depart = debut;
        debut += groupe.items.length;
        return (
          <div key={g}>
            {groupe.nom && <h3 className="mt-3 text-[15px] font-semibold">{groupe.nom}</h3>}
            <ol className="divide-y divide-ligne">
              {groupe.items.map((item, i) => (
                <li key={i} className="grid grid-cols-[2rem_minmax(0,1fr)] py-2">
                  <span className="font-semibold tabular-nums text-texte-2">{depart + i + 1}.</span>
                  <span className="extrait-exact block">{item}</span>
                </li>
              ))}
            </ol>
          </div>
        );
      })}
    </section>
  );
}

/** Coût et durée sur une même grille : une ligne par fiche, le détail des frais à la demande. */
function Faits({ analyse, t }: { analyse: Analyse; t: Textes }) {
  const couts = analyse.sections.filter((s) => s.genre === "cout");
  const durees = analyse.sections.filter((s) => s.genre === "duree");
  if (!couts.length && !durees.length) return null;

  const lignes = new Map<string, { cout?: string[]; duree?: string }>();
  couts.flatMap((s) => s.items).forEach((item) => {
    const { reference, texte } = separerExtrait(item);
    lignes.set(reference || "", { ...lignes.get(reference || ""), cout: texte.split(" ; ") });
  });
  durees.flatMap((s) => s.items).forEach((item) => {
    const { reference, texte } = separerExtrait(item);
    lignes.set(reference || "", { ...lignes.get(reference || ""), duree: texte });
  });
  const plusieurs = lignes.size > 1 || !lignes.has("");

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[15px]">
        <thead>
          <tr className="border-b-2 border-texte text-sm">
            {plusieurs && <th className="py-1.5 pr-4">{t.fiche}</th>}
            {couts[0] && <th className="py-1.5 pr-4">{couts[0].titre}</th>}
            {durees[0] && <th className="py-1.5">{durees[0].titre}</th>}
          </tr>
        </thead>
        <tbody>
          {Array.from(lignes.entries()).map(([fiche, ligne]) => (
            <tr key={fiche} className="border-b border-ligne align-top">
              {plusieurs && <td className="py-2 pr-4">{fiche}</td>}
              {couts[0] && (
                <td className="py-2 pr-4">
                  {ligne.cout && (
                    <>
                      <span className="extrait-exact block font-semibold">{ligne.cout[0]}</span>
                      {ligne.cout.length > 1 && (
                        <details className="mt-0.5 text-sm">
                          <summary className="text-accent">
                            {t.detail} ({ligne.cout.length - 1})
                          </summary>
                          <ul className="mt-1 space-y-0.5 text-texte-2">
                            {ligne.cout.slice(1).map((d, k) => (
                              <li key={k} className="extrait-exact">
                                {d}
                              </li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </>
                  )}
                </td>
              )}
              {durees[0] && <td className="whitespace-nowrap py-2 font-semibold">{ligne.duree}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Extraits({ section }: { section: Section }) {
  return (
    <section>
      <Titre2>{section.titre}</Titre2>
      <div className="mt-2 space-y-3">
        {section.items.map((item, i) => {
          const { reference, texte } = separerExtrait(item);
          return (
            <div key={i} className="border-l-2 border-ligne-forte pl-3">
              {reference && <p className="text-sm font-semibold">{reference}</p>}
              <p className="extrait-exact">{texte}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function OngletSources({ citations, t }: { citations: Citation[]; t: Textes }) {
  const documents = useMemo(() => {
    const parTitre = new Map<string, Citation[]>();
    citations.forEach((c) => parTitre.set(c.titre, [...(parTitre.get(c.titre) || []), c]));
    return Array.from(parTitre.entries());
  }, [citations]);

  return (
    <div className="space-y-6">
      {documents.map(([titre, extraits]) => (
        <section key={titre}>
          <div className="border-b-2 border-texte pb-1.5">
            <h2 className="font-bold">{titre}</h2>
            <p className="text-sm text-texte-2">{t.typesSource[extraits[0].type_source]}</p>
          </div>
          <ul className="divide-y divide-ligne">
            {extraits.map((c) => (
              <li key={c.id} className="py-2.5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4">
                  <span className="font-semibold">{c.article}</span>
                  <span className="text-sm">
                    <Etat ton={c.statut_verification === "verifie" ? "ok" : "attention"}>{c.statut_verification === "verifie" ? t.verifie : t.aVerifier}</Etat>
                  </span>
                </div>
                <p className="mt-0.5 text-texte-2">{c.texte}</p>
                <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-sm text-accent underline underline-offset-2">
                  {t.ouvrirSource}
                  <Icone nom="externe" taille={13} />
                </a>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function OngletControle({ audit, mode, t }: { audit: Audit; mode?: string; t: Textes }) {
  const gaps = audit.gaps.filter((g) => !audit.controles.some((c) => c.detail === g));
  const tons = { ok: "ok", reserve: "attention", echec: "erreur" } as const;
  const tonVerdict = audit.verdict === "conforme" ? "ok" : audit.verdict === "partiel" ? "attention" : "erreur";
  return (
    <div>
      <dl className="grid gap-x-8 gap-y-2 sm:grid-cols-3">
        <div>
          <dt className="text-sm text-texte-2">{t.controleVerdict}</dt>
          <dd className="font-semibold">
            <Etat ton={tonVerdict}>{t.verdicts[audit.verdict]}</Etat>
          </dd>
        </div>
        <div>
          <dt className="text-sm text-texte-2">{t.controleDecision}</dt>
          <dd className="font-semibold">{t.decisions[audit.decision]}</dd>
        </div>
        {mode && (
          <div>
            <dt className="text-sm text-texte-2">{t.controleMode}</dt>
            <dd className="font-semibold">{t.modes[mode] || mode}</dd>
          </div>
        )}
      </dl>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-texte text-sm">
              <th className="py-1.5 pr-4">{t.colonnesControle.controle}</th>
              <th className="py-1.5 pr-4">{t.colonnesControle.resultat}</th>
              <th className="py-1.5">{t.colonnesControle.detail}</th>
            </tr>
          </thead>
          <tbody>
            {audit.controles.map((c, i) => (
              <tr key={`${c.nom}${i}`} className="border-b border-ligne align-top">
                <td className="whitespace-nowrap py-2 pr-4 font-medium">{t.controles[c.nom] || c.nom}</td>
                <td className="py-2 pr-4">
                  <Etat ton={tons[c.resultat]}>{t.resultatsControle[c.resultat]}</Etat>
                </td>
                <td className="py-2 text-texte-2">{c.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {gaps.length > 0 && (
        <div className="mt-5">
          <h2 className="font-semibold">{t.autresPoints}</h2>
          <ul className="mt-1 list-disc pl-5 text-texte-2">
            {gaps.map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

type Onglet = "demarche" | "sources" | "controle" | "formulaire";

export function Fiche({ message, langue, consent }: { message: Message; langue: Langue; consent: boolean }) {
  const t = TEXTES[langue];
  const [onglet, setOnglet] = useState<Onglet>("demarche");
  const analyse = useMemo(() => analyser(message.content), [message.content]);
  const citations = message.citations || [];
  const controles = message.audit?.controles || [];
  const titre = message.procedure || analyse.titre;

  // L'état reflète ce qui est réellement cité : une seule source à vérifier suffit à le nuancer.
  const aVerifier = citations.some((c) => c.statut_verification !== "verifie");
  const etat: { ton: "ok" | "attention" | "erreur"; texte: string } | null =
    message.statut === "lacune"
      ? { ton: "erreur", texte: t.etats.lacune }
      : message.statut === "partiel"
        ? { ton: "attention", texte: t.etats.partiel }
        : aVerifier
          ? { ton: "attention", texte: t.etats.enPartie }
          : citations.length && message.type === "reponse"
            ? { ton: "ok", texte: t.etats.verifie }
            : null;

  const trouver = (genre: Section["genre"]) => analyse.sections.filter((s) => s.genre === genre);
  // Sans citation structurée, la liste des sources du texte reste le seul repère : on la garde.
  const autres = analyse.sections.filter((s) => s.genre === "liste" || (s.genre === "sources" && !citations.length));

  const onglets: { id: Onglet; libelle: string }[] = [
    { id: "demarche", libelle: t.onglets.demarche },
    ...(citations.length ? [{ id: "sources" as Onglet, libelle: `${t.onglets.sources} (${citations.length})` }] : []),
    ...(controles.length ? [{ id: "controle" as Onglet, libelle: `${t.onglets.controle} (${controles.length})` }] : []),
    ...(message.formulaire ? [{ id: "formulaire" as Onglet, libelle: t.onglets.formulaire }] : []),
  ];

  return (
    <article>
      <header className="px-4 pb-4 pt-5 lg:px-8">
        {titre && <h1 className="text-[26px] font-bold leading-tight">{titre}</h1>}
        <div className="mt-1.5 flex flex-wrap items-baseline gap-x-5 gap-y-1">
          {etat && (
            <span className="font-medium">
              <Etat ton={etat.ton}>{etat.texte}</Etat>
            </span>
          )}
          {analyse.cas && (
            <span className="text-texte-2">
              {t.votreCas} : <strong className="font-semibold text-texte">{analyse.cas}</strong>
            </span>
          )}
        </div>
      </header>

      <div role="tablist" aria-label={titre || t.fiche} className="sticky top-0 z-10 flex overflow-x-auto border-b border-ligne bg-surface px-4 lg:px-8">
        {onglets.map((o) => (
          <button
            key={o.id}
            role="tab"
            id={`onglet-${o.id}`}
            aria-selected={onglet === o.id}
            aria-controls="panneau-fiche"
            onClick={() => setOnglet(o.id)}
            className={`-mb-px whitespace-nowrap border-b-[3px] px-3 py-2.5 first:pl-0 ${onglet === o.id ? "border-accent font-semibold" : "border-transparent text-texte-2 hover:text-texte"}`}
          >
            {o.libelle}
          </button>
        ))}
      </div>

      <div role="tabpanel" id="panneau-fiche" aria-labelledby={`onglet-${onglet}`} className="max-w-[900px] px-4 py-5 lg:px-8">
        {onglet === "demarche" && (
          <div className="space-y-6">
            {analyse.alertes.map((alerte) => (
              <p key={alerte} className="extrait-exact border-l-[3px] border-[#c47f00] bg-attention-clair px-3 py-2">
                {alerte.replace(/^(Attention|Warning)\s*:\s*/, "")}
              </p>
            ))}
            {analyse.paragraphes.length > 0 && (
              <div className="space-y-2">
                {analyse.paragraphes.map((p, i) => (
                  <p key={i}>
                    <Riche texte={p} />
                  </p>
                ))}
              </div>
            )}
            <Faits analyse={analyse} t={t} />
            {trouver("pieces").map((s, i) => (
              <Pieces key={i} section={s} t={t} />
            ))}
            {trouver("etapes").map((s, i) => (
              <Etapes key={i} section={s} />
            ))}
            {trouver("extraits").map((s, i) => (
              <Extraits key={i} section={s} />
            ))}
            {autres.map((s, i) => (
              <section key={i}>
                {s.titre && <Titre2>{s.titre}</Titre2>}
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {s.items.map((item, j) => (
                    <li key={j}>
                      <Riche texte={item} />
                    </li>
                  ))}
                </ul>
              </section>
            ))}
            {analyse.notes.length > 0 && (
              <div className="space-y-1 border-t border-ligne pt-3 text-sm text-texte-2">
                {analyse.notes.map((note, i) => (
                  <p key={i}>
                    <Riche texte={note} />
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
        {onglet === "sources" && <OngletSources citations={citations} t={t} />}
        {onglet === "controle" && message.audit && <OngletControle audit={message.audit} mode={message.mode} t={t} />}
        {onglet === "formulaire" && message.formulaire && <FormulaireCitoyen initial={message.formulaire} langue={langue} consent={consent} />}
      </div>
    </article>
  );
}
