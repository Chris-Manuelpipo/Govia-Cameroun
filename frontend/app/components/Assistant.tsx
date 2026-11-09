"use client";
import { useEffect, useMemo, useRef } from "react";
import { Langue, Textes } from "../i18n";
import { confiance, panneauDe } from "../lib/confiance";
import { analyser } from "../lib/reponse";
import { DemarcheCatalogue, Message, Notice as TypeNotice, Vue } from "../types";
import { AucunTexte } from "./AucunTexte";
import { Echanges, OuvrirPanneau } from "./Echanges";
import { Fiche, Onglet } from "./Fiche";
import { Etat, Icone } from "./icones";
import { Notice } from "./Notice";
import { Precision } from "./Precision";

const MOBILE = "(max-width: 1023px)";

export interface Ouverture {
  /** Incrémenté à chaque ouverture demandée par l'utilisateur (et non à l'arrivée d'une réponse). */
  n: number;
  onglet: Onglet;
}

/**
 * Vue « dossier administratif » : à gauche les échanges, à droite le panneau qui s'ouvre quand une réponse
 * contient une procédure, une demande de précision ou un constat d'absence de texte.
 * Sur mobile, le panneau prend la place du fil et un lien ramène aux échanges.
 */
export function Assistant({
  langue,
  t,
  messages,
  selection,
  ouverture,
  feuille,
  saisie,
  chargement,
  consent,
  catalogue,
  notice,
  erreurNotice,
  enAttente,
  onSaisie,
  onEnvoyer,
  onEffacer,
  onLu,
  onOuvrir,
  onFermerFeuille,
  onAccepter,
  onRefuser,
  onRetirer,
  onVue,
}: {
  langue: Langue;
  t: Textes;
  messages: Message[];
  selection: number | null;
  ouverture: Ouverture;
  feuille: boolean;
  saisie: string;
  chargement: boolean;
  consent: boolean;
  catalogue: DemarcheCatalogue[];
  notice: TypeNotice | null;
  erreurNotice: boolean;
  enAttente: string | null;
  onSaisie: (texte: string) => void;
  onEnvoyer: (texte: string) => void;
  onEffacer: () => void;
  onLu: (index: number) => void;
  onOuvrir: OuvrirPanneau;
  onFermerFeuille: () => void;
  onAccepter: () => void;
  onRefuser: () => void;
  onRetirer: () => void;
  onVue: (v: Vue) => void;
}) {
  const champ = useRef<HTMLInputElement>(null);
  const fil = useRef<HTMLDivElement>(null);
  const panneau = useRef<HTMLElement>(null);
  const apres = useRef<"fil" | "champ" | null>(null);

  // Sur mobile, le panneau remplace le fil. Sans accord, il porte la notice : l'assistant n'a rien d'autre à montrer.
  const panneauVisible = !consent || feuille;
  const ouverte = selection !== null ? messages[selection] : null;
  const genre = ouverte ? panneauDe(ouverte) : null;
  const administration = ouverte?.procedureId ? catalogue.find((d) => d.id === ouverte.procedureId)?.autorite ?? null : null;
  const suivant = selection !== null ? messages[selection + 1] : undefined;
  const reponduePar = suivant?.role === "user" ? suivant.content : null;

  // Annonce vocale : un résumé court de la dernière réponse, plutôt que tout le fil relu à chaque ajout.
  const dernier = messages[messages.length - 1];
  const annonce = useMemo(() => {
    if (!dernier || dernier.role !== "agent") return "";
    if (dernier.chargement) return t.recherche;
    if (dernier.erreur) return "";
    const type = panneauDe(dernier);
    if (type === "precision") return t.annoncePrecision;
    if (type === "aucun") return t.annonceAucun;
    if (type === "fiche") {
      const niveau = confiance(dernier);
      return t.annonceReponse(dernier.procedure || analyser(dernier.content).titre || t.textesProches, niveau ? t.confiance[niveau.niveau].libelle : "");
    }
    return dernier.content.replace(/\*\*/g, "");
  }, [dernier, t]);

  // Une réponse haute ne chasse pas la question : le fil se cale sur le début du dernier échange.
  // Sur grand écran on fait défiler le seul cadre du fil : scrollIntoView déplacerait aussi la page, qui ne défile pas.
  useEffect(() => {
    const cadre = fil.current;
    const dernier = cadre?.querySelector<HTMLElement>(":scope > ol > li:last-child");
    if (!cadre || !dernier) return;
    if (window.matchMedia(MOBILE).matches) dernier.scrollIntoView({ block: "start" });
    else cadre.scrollTop += dernier.getBoundingClientRect().top - cadre.getBoundingClientRect().top - 8;
  }, [messages.length, chargement, feuille]);

  // Une fiche se lit depuis son début, sur grand écran comme sur téléphone.
  useEffect(() => {
    if (selection === null || !panneau.current) return;
    panneau.current.scrollTop = 0;
    if (feuille && window.matchMedia(MOBILE).matches) panneau.current.scrollIntoView({ block: "start" });
  }, [selection, feuille, ouverture.n]);

  // Le focus suit le panneau quand l'utilisateur l'ouvre, et toujours sur mobile où il remplace le fil.
  useEffect(() => {
    if (ouverture.n > 0) panneau.current?.focus({ preventScroll: true });
  }, [ouverture.n]);
  useEffect(() => {
    if (feuille && window.matchMedia(MOBILE).matches) panneau.current?.focus({ preventScroll: true });
  }, [feuille, selection]);

  function focaliser(cible: "fil" | "champ") {
    (cible === "champ" ? champ.current : fil.current)?.focus({ preventScroll: true });
  }
  useEffect(() => {
    if (!feuille && apres.current) {
      focaliser(apres.current);
      apres.current = null;
    }
  }, [feuille]);

  /** Ferme le panneau sur mobile, puis place le focus. Sur grand écran, le panneau reste : seul le focus bouge. */
  function revenir(cible: "fil" | "champ") {
    if (feuille) {
      apres.current = cible;
      onFermerFeuille();
    } else focaliser(cible);
  }

  return (
    <div className="lg:grid lg:h-full lg:grid-cols-[minmax(340px,400px)_minmax(0,1fr)]">
      <p role="status" className="sr-only">
        {annonce}
      </p>

      {/* Échanges */}
      <section aria-label={t.echanges} className={`${panneauVisible ? "hidden" : "flex"} min-h-[60vh] flex-col bg-fond lg:flex lg:h-full lg:min-h-0 lg:border-r lg:border-ligne`}>
        <div className="flex shrink-0 items-center justify-between border-b border-ligne bg-surface px-4">
          <h2 className="py-2.5 text-[15px] font-semibold">{t.echanges}</h2>
          {messages.length > 0 && (
            <button onClick={onEffacer} disabled={chargement} className="min-h-[44px] px-1 text-accent underline underline-offset-2 disabled:opacity-50">
              {t.effacer}
            </button>
          )}
        </div>

        <div ref={fil} tabIndex={0} className="flex-1 pb-32 lg:min-h-0 lg:overflow-y-auto lg:pb-0">
          {messages.length === 0 ? <p className="px-4 py-4 text-sm text-texte-2">{t.aucunEchange}</p> : <Echanges messages={messages} selection={selection} occupe={chargement} t={t} onOuvrir={onOuvrir} onEnvoyer={onEnvoyer} onLu={onLu} />}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            onEnvoyer(saisie);
          }}
          className="fixed inset-x-0 bottom-0 z-20 shrink-0 border-t border-ligne bg-surface p-3 lg:static"
        >
          {!consent && (
            <p className="mb-2 flex items-start gap-2 text-[13px] text-texte-2">
              <Icone nom="cadenas" taille={15} className="mt-0.5 text-attention-vif" />
              {t.saisieBloquee}
            </p>
          )}
          <div className="flex gap-2">
            <input
              ref={champ}
              type="text"
              value={saisie}
              maxLength={1000}
              disabled={!consent}
              onChange={(e) => onSaisie(e.target.value)}
              placeholder={consent ? t.placeholder : t.placeholderBloque}
              aria-label={t.champ}
              enterKeyHint="send"
              className="h-11 min-w-0 flex-1 border border-ligne-forte bg-surface px-3 placeholder:text-texte-2 disabled:cursor-not-allowed disabled:bg-fond"
            />
            <button
              type="submit"
              disabled={!consent || chargement || !saisie.trim()}
              className="inline-flex h-11 shrink-0 items-center gap-2 bg-bouton px-4 font-semibold text-white hover:bg-bouton-fonce disabled:cursor-not-allowed disabled:bg-desactive disabled:text-sur-desactive"
            >
              {t.envoyer}
              <Icone nom="envoyer" taille={16} />
            </button>
          </div>
        </form>
      </section>

      {/* Panneau : fiche, précision requise, aucun texte ouvert, ou accueil */}
      <section
        ref={panneau}
        tabIndex={0}
        aria-label={t.fiche}
        className={`fond-motif ${panneauVisible ? "block" : "hidden"} scroll-mt-[var(--nav-h)] lg:block lg:h-full lg:overflow-y-auto`}
      >
        {consent && (
          <div className="border-b border-ligne bg-surface lg:hidden">
            <button onClick={() => revenir("fil")} className="flex min-h-[48px] items-center gap-2 px-4 font-medium text-accent">
              <Icone nom="retour" taille={18} />
              {t.retourEchanges}
            </button>
          </div>
        )}

        {!consent ? (
          <div className="mx-auto max-w-[900px] px-0 py-0 sm:px-4 sm:py-6 lg:px-8">
            <Notice notice={notice} erreur={erreurNotice} langue={langue} consent={consent} enAttente={enAttente} onAccepter={onAccepter} onRefuser={onRefuser} onRetirer={onRetirer} />
          </div>
        ) : ouverte && genre === "fiche" ? (
          <Fiche key={`${selection}-${ouverture.n}`} message={ouverte} langue={langue} consent={consent} administration={administration} ongletInitial={ouverture.onglet} anime={!!ouverte.nouveau} onFini={() => onLu(selection as number)} />
        ) : ouverte && genre === "precision" ? (
          <Precision key={selection} message={ouverte} reponduePar={reponduePar} occupe={chargement} t={t} onChoisir={onEnvoyer} onReformuler={() => revenir("champ")} />
        ) : ouverte && genre === "aucun" ? (
          <AucunTexte key={selection} message={ouverte} t={t} onAutreQuestion={() => revenir("champ")} />
        ) : (
          <div className="mx-auto max-w-[800px] px-0 py-0 sm:px-4 sm:py-6 lg:px-8 lg:py-8">
            <div className="border border-ligne bg-surface px-5 py-6 sm:px-7">
              <h1 className="text-[26px] font-bold leading-tight text-titre">{t.assistantTitre}</h1>
              <p className="mt-2 text-texte-2">{t.assistantTexte}</p>
              <p className="mt-1 text-[14px] text-texte-2">{t.assistantLimites}</p>

              <h2 className="mt-6 border-b-2 border-titre pb-1.5 text-[17px] font-bold">{t.exemplesTitre}</h2>
              <ul className="divide-y divide-ligne">
                {t.exemples.map((exemple) => (
                  <li key={exemple}>
                    <button
                      disabled={chargement}
                      onClick={() => onEnvoyer(exemple)}
                      className="flex min-h-[48px] w-full items-center justify-between gap-3 py-2 text-left font-medium text-accent hover:bg-fond disabled:opacity-50"
                    >
                      {exemple}
                      <Icone nom="envoyer" taille={16} />
                    </button>
                  </li>
                ))}
              </ul>

              <p className="mt-4 flex flex-wrap items-center gap-x-2 text-sm text-texte-2">
                <Etat ton="ok">{t.accordDonne}</Etat>
                <span aria-hidden="true">·</span>
                <button onClick={() => onVue("donnees")} className="inline-flex min-h-[44px] items-center text-accent underline underline-offset-2">
                  {t.vuesLongues.donnees}
                </button>
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
