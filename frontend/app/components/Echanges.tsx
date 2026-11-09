"use client";
import { Textes } from "../i18n";
import { confiance, documentsCites, panneauDe } from "../lib/confiance";
import { analyser, compter } from "../lib/reponse";
import { Message } from "../types";
import { ConfianceEnLigne, STYLE_CONFIANCE } from "./Confiance";
import { Icone } from "./icones";
import { SourcesCitees } from "./SourcesCitees";

export type OuvrirPanneau = (index: number, onglet?: "sources") => void;

const ETIQUETTE = "mb-0.5 text-[12px] font-bold uppercase tracking-wider text-texte-2";

function BulleUtilisateur({ texte, t }: { texte: string; t: Textes }) {
  return (
    <div className="flex flex-col items-end">
      <p className="mb-0.5 text-[12px] font-semibold text-texte-2">{t.vous}</p>
      <p className="max-w-[90%] whitespace-pre-wrap break-words border border-[#b4cde6] bg-accent-clair px-3 py-2 text-texte">{texte}</p>
    </div>
  );
}

/** Cadre d'une réponse : filets fins, 3 px de rayon, une barre à gauche qui porte l'état. */
function Cadre({ barre, fond = "bg-surface", children, ...reste }: { barre: string; fond?: string; children: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div {...reste} className={`border border-l-4 border-ligne ${barre} ${fond}`}>
      {children}
    </div>
  );
}

function BoutonPanneau({ ouverte, onClick, children }: { ouverte: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      aria-current={ouverte ? "true" : undefined}
      className={`mt-2.5 flex min-h-[44px] w-full items-center justify-between gap-2 border px-3 text-left font-semibold ${
        ouverte ? "border-accent bg-accent-clair text-accent-fonce" : "border-accent text-accent hover:bg-accent-clair"
      }`}
    >
      <span>{children}</span>
      <Icone nom="envoyer" taille={16} />
    </button>
  );
}

function BulleAgent({
  message,
  index,
  suivant,
  selection,
  t,
  onOuvrir,
}: {
  message: Message;
  index: number;
  suivant?: Message;
  selection: number | null;
  t: Textes;
  onOuvrir: OuvrirPanneau;
}) {
  const etiquette = <p className={ETIQUETTE}>{t.govia}</p>;

  if (message.chargement) {
    return (
      <div className="mt-3">
        {etiquette}
        <Cadre barre="border-l-ligne-forte" data-chargement>
          <p className="flex items-center gap-2 px-3 py-2.5 text-texte-2">
            <span className="indicateur-chargement" aria-hidden="true" />
            {t.recherche}
          </p>
        </Cadre>
      </div>
    );
  }

  if (message.erreur) {
    return (
      <div className="mt-3">
        {etiquette}
        <Cadre barre="border-l-erreur" fond="bg-erreur-clair" role="alert">
          <p className="px-3 py-2.5 text-erreur">{message.content}</p>
        </Cadre>
      </div>
    );
  }

  const panneau = panneauDe(message);
  const niveau = confiance(message);
  const ouverte = selection === index;

  // Refus, réponse sans panneau : un simple texte, sans indicateur.
  if (!panneau) {
    return (
      <div className="mt-3">
        {etiquette}
        <Cadre barre="border-l-ligne-forte">
          <div className="flex items-start gap-2 px-3 py-2.5">
            <Icone nom="info" taille={18} className="mt-0.5 text-texte-2" />
            <p className="min-w-0 whitespace-pre-wrap break-words">{message.content.replace(/\*\*/g, "")}</p>
          </div>
        </Cadre>
      </div>
    );
  }

  // Précision requise : l'agent attend un choix ; il s'ouvre dans le panneau.
  if (panneau === "precision") {
    const repondue = suivant?.role === "user";
    return (
      <div className="mt-3">
        {etiquette}
        <Cadre barre="border-l-jaune">
          <div className="px-3 pb-3 pt-2.5">
            <p className="flex items-center gap-2 text-[14px] font-semibold">
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-jaune text-marine">
                <Icone nom="interrogation" taille={16} epaisseur={2.6} />
              </span>
              {t.precision.surtitre}
            </p>
            <p className="mt-1.5">{message.content}</p>
            {repondue ? (
              <p className="mt-1.5 flex items-center gap-1.5 text-[14px] font-medium text-ok-fonce">
                <Icone nom="coche-cercle" taille={16} className="text-ok" />
                {t.precision.repondue}
              </p>
            ) : (
              <BoutonPanneau ouverte={ouverte} onClick={() => onOuvrir(index)}>
                <span className={ouverte ? "lg:hidden" : ""}>{t.precision.voirOptions}</span>
                {ouverte && <span className="hidden lg:inline">{t.precision.affichee}</span>}
              </BoutonPanneau>
            )}
          </div>
        </Cadre>
      </div>
    );
  }

  const style = niveau ? STYLE_CONFIANCE[niveau.niveau] : STYLE_CONFIANCE.aucun;

  // Aucun texte ouvert : la bulle le dit, le détail est dans le panneau.
  if (panneau === "aucun") {
    return (
      <div className="mt-3">
        {etiquette}
        <Cadre barre={style.barre}>
          <div className="px-3 pb-3 pt-2.5">
            {niveau && <ConfianceEnLigne confiance={niveau} t={t} />}
            {message.procedure && <p className="mt-1.5 text-[16px] font-bold leading-snug">{message.procedure}</p>}
            <p className="mt-1 text-[14px] text-texte-2">{t.confiance.aucun.detail}</p>
            <BoutonPanneau ouverte={ouverte} onClick={() => onOuvrir(index)}>
              <span className={ouverte ? "lg:hidden" : ""}>{t.voirPistes}</span>
              {ouverte && <span className="hidden lg:inline">{t.pistesAffichees}</span>}
            </BoutonPanneau>
          </div>
        </Cadre>
      </div>
    );
  }

  // Réponse sourcée (ou textes proches) : titre, état, résumé, puis le pied « Sources » intégré.
  const analyse = analyser(message.content);
  const titre = message.procedure || analyse.titre;
  const nombreEtapes = compter(analyse, "etapes") || message.etapes?.length || 0;
  const nombrePieces = compter(analyse, "pieces") || message.pieces?.length || 0;
  const resume = [nombreEtapes ? t.etapesN(nombreEtapes) : "", nombrePieces ? t.piecesN(nombrePieces) : ""].filter(Boolean).join(" · ");
  const documents = documentsCites(message.citations || []);

  return (
    <div className="mt-3">
      {etiquette}
      <Cadre barre={style.barre}>
        <div className="px-3 pb-3 pt-2.5">
          {niveau && <ConfianceEnLigne confiance={niveau} t={t} />}
          <p className="mt-1.5 text-[16px] font-bold leading-snug">{titre || t.textesProches}</p>
          {analyse.cas && (
            <p className="mt-0.5 text-[14px] text-texte-2">
              {t.votreCas} : <strong className="font-semibold text-texte">{analyse.cas}</strong>
            </p>
          )}
          {resume && <p className="mt-0.5 text-[14px] text-texte-2">{resume}</p>}
          <BoutonPanneau ouverte={ouverte} onClick={() => onOuvrir(index)}>
            <span className={ouverte ? "lg:hidden" : ""}>{t.voirFiche}</span>
            {ouverte && <span className="hidden lg:inline">{t.ficheOuverte}</span>}
          </BoutonPanneau>
        </div>
        <SourcesCitees documents={documents} t={t} max={3} onTout={() => onOuvrir(index, "sources")} />
      </Cadre>
    </div>
  );
}

/** Le fil : chaque question de l'utilisateur, suivie de la réponse de l'agent. */
export function Echanges({ messages, selection, t, onOuvrir }: { messages: Message[]; selection: number | null; t: Textes; onOuvrir: OuvrirPanneau }) {
  return (
    <ol className="space-y-6 px-4 py-4">
      {messages.map((m, i) =>
        m.role === "user" ? (
          <li key={i} className="scroll-mt-[calc(var(--nav-h)+8px)]">
            <BulleUtilisateur texte={m.content} t={t} />
            {messages[i + 1] && <BulleAgent message={messages[i + 1]} index={i + 1} suivant={messages[i + 2]} selection={selection} t={t} onOuvrir={onOuvrir} />}
          </li>
        ) : null,
      )}
    </ol>
  );
}
