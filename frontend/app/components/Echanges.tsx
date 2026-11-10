"use client";
import { Textes } from "../i18n";
import { confiance, documentsCites, panneauDe } from "../lib/confiance";
import { analyser, compter } from "../lib/reponse";
import { Message, Option } from "../types";
import { ConfianceEnLigne, STYLE_CONFIANCE } from "./Confiance";
import { Icone } from "./icones";
import { SourcesCitees } from "./SourcesCitees";
import { TexteProgressif } from "./TexteProgressif";

export type OuvrirPanneau = (index: number, onglet?: "sources") => void;

function BulleUtilisateur({ texte, t }: { texte: string; t: Textes }) {
  return (
    <p className="ml-auto w-fit max-w-[90%] whitespace-pre-wrap break-words border border-bulle bg-accent-clair px-3 py-2 text-texte">
      <span className="sr-only">{t.vous} : </span>
      {texte}
    </p>
  );
}

/** Cadre d'une réponse : filets fins, 3 px de rayon, une barre à gauche qui porte l'état. */
function Cadre({ barre, fond = "bg-surface", children, ...reste }: { barre: string; fond?: string; children: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div {...reste} className={`mt-2 border border-l-4 border-ligne ${barre} ${fond}`}>
      {children}
    </div>
  );
}

/**
 * Lien d'action discret : pas de cadre, seulement du texte et une flèche.
 * Sur mobile, le panneau ouvert est caché dès qu'on revient au fil : le lien reste donc actif
 * à cette taille. Sur grand écran, le panneau est visible à côté et le lien devient un simple état.
 */
function BoutonPanneau({ ouverte, onClick, voir, affiche }: { ouverte: boolean; onClick: () => void; voir: string; affiche: string }) {
  const lien = (
    <>
      <span>{voir}</span>
      <Icone nom="envoyer" taille={16} />
    </>
  );
  return (
    <button
      onClick={onClick}
      aria-current={ouverte ? "true" : undefined}
      className={`-ml-1 mt-1 inline-flex min-h-[44px] items-center gap-1.5 px-1 font-semibold hover:underline ${ouverte ? "text-accent lg:text-texte-2" : "text-accent"}`}
    >
      {ouverte ? (
        <>
          <span className="inline-flex items-center gap-1.5 lg:hidden">{lien}</span>
          <span className="hidden lg:inline">{affiche}</span>
        </>
      ) : (
        lien
      )}
    </button>
  );
}

/** Réponses rapides proposées par l'agent : un clic envoie la question. */
function Puces({ options, desactive, onEnvoyer }: { options: Option[]; desactive: boolean; onEnvoyer: (texte: string) => void }) {
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o.message}
          disabled={desactive}
          onClick={() => onEnvoyer(o.message)}
          className="min-h-[44px] border border-ligne-forte bg-surface px-3 text-left text-[14px] font-medium text-accent hover:bg-accent-clair disabled:cursor-not-allowed disabled:opacity-50"
        >
          {o.libelle}
        </button>
      ))}
    </div>
  );
}

function BulleAgent({
  message,
  index,
  suivant,
  selection,
  occupe,
  t,
  onOuvrir,
  onEnvoyer,
  onLu,
}: {
  message: Message;
  index: number;
  suivant?: Message;
  selection: number | null;
  occupe: boolean;
  t: Textes;
  onOuvrir: OuvrirPanneau;
  onEnvoyer: (texte: string) => void;
  onLu: (index: number) => void;
}) {
  const nom = <span className="sr-only">{t.govia} : </span>;

  if (message.chargement) {
    return (
      <Cadre barre="border-l-ligne-forte" data-chargement>
        <p className="flex items-center gap-2 px-3 py-2.5 text-texte-2">
          <span className="indicateur-chargement" aria-hidden="true" />
          {nom}
          {t.recherche}
        </p>
      </Cadre>
    );
  }

  if (message.erreur) {
    return (
      <Cadre barre="border-l-erreur" fond="bg-erreur-clair" role="alert">
        <p className="px-3 py-2.5 text-erreur">{message.content}</p>
      </Cadre>
    );
  }

  const panneau = panneauDe(message);
  const niveau = confiance(message);
  const ouverte = selection === index;

  // Conversation, refus, hors périmètre : un texte simple, et au besoin des exemples à cliquer.
  if (!panneau) {
    return (
      <Cadre barre="border-l-ligne-forte">
        <div className="px-3 py-2.5">
          <p className="whitespace-pre-wrap break-words">
            {nom}
            <TexteProgressif texte={message.content.replace(/\*\*/g, "")} anime={!!message.nouveau} onFini={() => onLu(index)} />
          </p>
          {!suivant && !message.nouveau && !!message.options?.length && <Puces options={message.options} desactive={occupe} onEnvoyer={onEnvoyer} />}
        </div>
      </Cadre>
    );
  }

  // Précision requise : l'agent attend un choix ; il s'ouvre dans le panneau.
  if (panneau === "precision") {
    const repondue = suivant?.role === "user";
    return (
      <Cadre barre="border-l-jaune">
        <div className="px-3 pb-2 pt-2.5">
          <p className="flex items-center gap-2 font-semibold">
            <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-jaune text-marine">
              <Icone nom="interrogation" taille={16} epaisseur={2.6} />
            </span>
            {nom}
            {t.precision.surtitre}
          </p>
          <p className="mt-1.5">{message.content}</p>
          {repondue ? (
            <p className="mt-1.5 flex items-center gap-1.5 text-[14px] text-texte-2">
              <Icone nom="coche-cercle" taille={16} className="text-ok" />
              {t.precision.repondue}
            </p>
          ) : (
            <BoutonPanneau ouverte={ouverte} onClick={() => onOuvrir(index)} voir={t.precision.voirOptions} affiche={t.precision.affichee} />
          )}
        </div>
      </Cadre>
    );
  }

  const style = niveau ? STYLE_CONFIANCE[niveau.niveau] : STYLE_CONFIANCE.aucun;

  // Aucun texte ouvert : la bulle le dit, le détail est dans le panneau.
  if (panneau === "aucun") {
    return (
      <Cadre barre={style.barre}>
        <div className="px-3 pb-2 pt-2.5">
          {nom}
          {niveau && <ConfianceEnLigne confiance={niveau} t={t} />}
          {message.procedure && <p className="mt-1 text-[16px] font-bold leading-snug">{message.procedure}</p>}
          <BoutonPanneau ouverte={ouverte} onClick={() => onOuvrir(index)} voir={t.voirPistes} affiche={t.pistesAffichees} />
        </div>
      </Cadre>
    );
  }

  // Réponse sourcée (ou textes proches) : état, titre, une ligne de résumé, puis le pied « Sources » intégré.
  const analyse = analyser(message.content);
  const titre = message.procedure || analyse.titre;
  const nombreEtapes = compter(analyse, "etapes") || message.etapes?.length || 0;
  const nombrePieces = compter(analyse, "pieces") || message.pieces?.length || 0;
  const resumeChiffre = [analyse.cas, nombreEtapes ? t.etapesN(nombreEtapes) : "", nombrePieces ? t.piecesN(nombrePieces) : ""].filter(Boolean).join(" · ");
  // La bulle montre la phrase d'introduction de la réponse ; à défaut, les chiffres.
  const intro = (analyse.paragraphes.find((p) => !/^[#|•-]/.test(p.trim())) || "")
    .replace(/\*\*/g, "")
    .replace(/[\[【][^\]】]*[\]】]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  const resume = intro.length > 20 ? intro : resumeChiffre;
  const documents = documentsCites(message.citations || []);

  return (
    <Cadre barre={style.barre}>
      <div className="px-3 pb-2 pt-2.5">
        {nom}
        {niveau && <ConfianceEnLigne confiance={niveau} t={t} />}
        {/* Sur grand écran, la fiche ouverte à côté porte déjà ce titre. */}
        <p className={`mt-1 text-[16px] font-bold leading-snug ${ouverte ? "lg:hidden" : ""}`}>{titre || t.textesProches}</p>
        {resume && <p className="mt-0.5 line-clamp-3 text-[14px] text-texte-2">{resume}</p>}
        <BoutonPanneau ouverte={ouverte} onClick={() => onOuvrir(index)} voir={t.voirFiche} affiche={t.ficheOuverte} />
      </div>
      <SourcesCitees documents={documents} t={t} max={3} compact onTout={() => onOuvrir(index, "sources")} />
    </Cadre>
  );
}

/** Le fil : chaque question de l'utilisateur, suivie de la réponse de l'agent. */
export function Echanges({
  messages,
  selection,
  occupe,
  t,
  onOuvrir,
  onEnvoyer,
  onLu,
}: {
  messages: Message[];
  selection: number | null;
  occupe: boolean;
  t: Textes;
  onOuvrir: OuvrirPanneau;
  onEnvoyer: (texte: string) => void;
  onLu: (index: number) => void;
}) {
  return (
    <ol className="space-y-5 px-4 py-4">
      {messages.map((m, i) =>
        m.role === "user" ? (
          <li key={i} className="scroll-mt-[calc(var(--nav-h)+8px)]">
            <BulleUtilisateur texte={m.content} t={t} />
            {messages[i + 1] && (
              <BulleAgent message={messages[i + 1]} index={i + 1} suivant={messages[i + 2]} selection={selection} occupe={occupe} t={t} onOuvrir={onOuvrir} onEnvoyer={onEnvoyer} onLu={onLu} />
            )}
          </li>
        ) : null,
      )}
    </ol>
  );
}
