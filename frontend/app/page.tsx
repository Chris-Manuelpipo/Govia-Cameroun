"use client";
import { useEffect, useRef, useState } from "react";
import { Annuaire } from "./components/Annuaire";
import { Fiche } from "./components/Fiche";
import { Etat, Marque } from "./components/icones";
import { ListeSources } from "./components/ListeSources";
import { Notice } from "./components/Notice";
import { analyser } from "./lib/reponse";
import { Langue, TEXTES, Textes } from "./i18n";
import { DemarcheCatalogue, DocumentSource, Message, Notice as TypeNotice, Stats, Vue } from "./types";

const VUES: Vue[] = ["demarches", "assistant", "sources", "donnees"];

/** Une réponse qui s'ouvre comme une fiche ; les autres (précision, refus) restent dans le fil. */
const estFiche = (m: Message) => m.type === "reponse" || m.type === "lacune" || !!m.citations?.length;

function ReponseDansLeFil({
  message,
  index,
  selection,
  occupe,
  consent,
  t,
  onSelection,
  onOption,
}: {
  message: Message;
  index: number;
  selection: number | null;
  occupe: boolean;
  consent: boolean;
  t: Textes;
  onSelection: (index: number) => void;
  onOption: (texte: string) => void;
}) {
  if (message.chargement) {
    return (
      <p data-chargement className="flex items-center gap-2 text-texte-2">
        <span className="indicateur-chargement" aria-hidden="true" />
        {t.recherche}
      </p>
    );
  }
  if (message.erreur) {
    return (
      <p role="alert" className="border-l-[3px] border-erreur bg-erreur-clair px-3 py-2 text-erreur">
        {message.content}
      </p>
    );
  }
  if (estFiche(message)) {
    const ouverte = selection === index;
    const analyse = analyser(message.content);
    const titre = message.procedure || analyse.titre || analyse.paragraphes[0] || t.fiche;
    const nombre = message.citations?.length || 0;
    return (
      <button
        onClick={() => onSelection(index)}
        aria-current={ouverte ? "true" : undefined}
        className={`block w-full border-l-[3px] py-1.5 pl-2.5 pr-2 text-left ${ouverte ? "border-accent bg-accent-clair" : "border-ligne-forte hover:bg-surface"}`}
      >
        <span className="block font-medium text-accent-fonce">{titre}</span>
        <span className="block text-[13px] text-texte-2">
          {nombre > 0 && `${t.resumeFiche(nombre)} · `}
          {ouverte ? t.ficheOuverte : t.voirFiche}
        </span>
      </button>
    );
  }
  return (
    <div>
      <p>{message.content.replace(/\*\*/g, "")}</p>
      {!!message.options?.length && (
        <ul className="mt-2 divide-y divide-ligne border border-ligne bg-surface">
          {message.options.map((o) => (
            <li key={o.message}>
              <button
                disabled={occupe || !consent}
                onClick={() => onOption(o.message)}
                className="block w-full px-3 py-2 text-left font-medium text-accent hover:bg-accent-clair disabled:cursor-not-allowed disabled:opacity-50"
              >
                {o.libelle}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Home() {
  const [vue, setVue] = useState<Vue>("demarches");
  const [langue, setLangue] = useState<Langue>("FR");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selection, setSelection] = useState<number | null>(null);
  const [saisie, setSaisie] = useState("");
  const [chargement, setChargement] = useState(false);
  const [consent, setConsent] = useState(false);
  const [enAttente, setEnAttente] = useState<string | null>(null);
  const [notice, setNotice] = useState<TypeNotice | null>(null);
  const [erreurNotice, setErreurNotice] = useState(false);
  const [catalogue, setCatalogue] = useState<DemarcheCatalogue[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [documents, setDocuments] = useState<DocumentSource[]>([]);
  const [erreurDocuments, setErreurDocuments] = useState(false);
  const finDuFil = useRef<HTMLDivElement>(null);
  const panneau = useRef<HTMLElement>(null);
  const contenu = useRef<HTMLElement>(null);
  const t = TEXTES[langue];

  useEffect(() => {
    document.documentElement.lang = langue.toLowerCase();
    setErreurNotice(false);
    fetch(`/api/consentement?langue=${langue}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setNotice)
      .catch(() => {
        setNotice(null);
        setErreurNotice(true);
      });
  }, [langue]);

  useEffect(() => {
    fetch("/api/catalogue")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setCatalogue)
      .catch(() => setCatalogue([]));
    fetch("/api/stats")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setStats)
      .catch(() => setStats(null));
    fetch("/api/documents")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((index) => setDocuments(index.documents))
      .catch(() => setErreurDocuments(true));
  }, []);

  useEffect(() => {
    finDuFil.current?.scrollIntoView({ block: "nearest" });
  }, [messages.length, chargement]);

  // Une fiche se lit depuis son début, sur grand écran comme sur téléphone.
  useEffect(() => {
    if (selection === null || !panneau.current) return;
    panneau.current.scrollTop = 0;
    panneau.current.scrollIntoView({ block: "start" });
  }, [selection]);

  useEffect(() => {
    contenu.current?.scrollTo(0, 0);
    window.scrollTo(0, 0);
  }, [vue]);

  function effacer() {
    setMessages([]);
    setSelection(null);
  }

  function retirerConsentement() {
    setConsent(false);
    setEnAttente(null);
    setSaisie("");
    effacer();
  }

  function refuser() {
    setEnAttente(null);
    setVue("demarches");
  }

  function accepter() {
    setConsent(true);
    setVue("assistant");
    if (enAttente) {
      const question = enAttente;
      setEnAttente(null);
      envoyer(question, true);
    }
  }

  /** Depuis l'annuaire : sans accord, la demande attend et rien n'est envoyé. */
  function ouvrir(texte: string) {
    setVue("assistant");
    if (consent) envoyer(texte);
    else setEnAttente(texte);
  }

  async function envoyer(texte: string, accord: boolean = consent) {
    if (!accord || chargement || !texte.trim()) return;

    // L'historique permet de répondre à une question de précision de l'agent.
    const historique = messages
      .filter((m) => !m.chargement && !m.erreur)
      .slice(-8)
      .map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.content.slice(0, 3900) }));
    const indexReponse = messages.length + 1;

    setMessages((liste) => [...liste, { role: "user", content: texte }, { role: "agent", content: "", chargement: true }]);
    setSaisie("");
    setChargement(true);

    const remplacer = (message: Message) => setMessages((liste) => [...liste.slice(0, -1), message]);
    try {
      const reponse = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...historique, { role: "user", content: texte }],
          consentement: accord,
          language: langue,
        }),
      });
      const corps = await reponse.json();
      if (!reponse.ok) {
        remplacer({ role: "agent", erreur: true, content: typeof corps.detail === "string" ? corps.detail : t.erreurService });
        return;
      }
      const message: Message = {
        role: "agent",
        content: corps.agent.reponse,
        type: corps.agent.type_reponse,
        procedure: corps.agent.procedure_identifiee,
        statut: corps.agent.statut_demarche,
        mode: corps.agent.mode_generation,
        options: corps.agent.options,
        citations: corps.agent.citations,
        audit: corps.audit,
        formulaire: corps.agent.formulaire_prerempli,
      };
      remplacer(message);
      if (estFiche(message)) setSelection(indexReponse);
    } catch {
      remplacer({ role: "agent", erreur: true, content: t.erreurConnexion });
    } finally {
      setChargement(false);
    }
  }

  const ficheOuverte = selection !== null ? messages[selection] : null;

  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:overflow-hidden">
      <header className="shrink-0">
        {/* Bande aux couleurs nationales, étoile au centre */}
        <div className="relative flex h-1.5" aria-hidden="true">
          <span className="flex-1 bg-[#007a3d]" />
          <span className="flex-1 bg-[#ce1126]" />
          <span className="flex-1 bg-[#fcd116]" />
          <svg viewBox="0 0 10 10" className="absolute left-1/2 top-0 h-1.5 w-1.5 -translate-x-1/2 fill-[#fcd116]">
            <path d="M5 0l1.2 3.6H10L6.9 5.8 8.1 9.5 5 7.2 1.9 9.5 3.1 5.8 0 3.6h3.8z" />
          </svg>
        </div>
        <div className="border-b border-ligne bg-fond">
          <div className="mx-auto grid max-w-[1000px] grid-cols-[1fr_auto_1fr] items-center gap-4 px-4 py-2.5 text-[12px] leading-snug">
            <div lang="fr">
              <p className="font-bold uppercase tracking-wide text-texte">République du Cameroun</p>
              <p className="italic text-texte-2">Paix – Travail – Patrie</p>
            </div>
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-marine">
              <Marque taille={22} />
            </span>
            <div lang="en" className="text-right">
              <p className="font-bold uppercase tracking-wide text-texte">Republic of Cameroon</p>
              <p className="italic text-texte-2">Peace – Work – Fatherland</p>
            </div>
          </div>
        </div>
        <div className="relative border-b border-ligne bg-surface px-4 py-2.5 text-center">
          <p className="text-[20px] font-bold uppercase tracking-wide text-marine">GOVIA Cameroun</p>
          <p className="text-sm font-medium text-accent">{t.sousTitre}</p>
          <div role="group" aria-label="Langue / Language" className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-0.5 text-sm lg:right-6">
            {(["FR", "EN"] as Langue[]).map((l) => (
              <button
                key={l}
                onClick={() => setLangue(l)}
                aria-pressed={langue === l}
                className={`h-8 min-w-[36px] rounded px-2 ${langue === l ? "bg-marine font-semibold text-white" : "text-texte-2 hover:text-texte"}`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
        <nav aria-label={t.navigation} className="border-b border-ligne bg-surface">
          <ul className="sans-barre flex overflow-x-auto px-4 lg:justify-center lg:px-6">
            {VUES.map((v) => (
              <li key={v}>
                <button
                  onClick={() => setVue(v)}
                  aria-current={vue === v ? "page" : undefined}
                  className={`-mb-px whitespace-nowrap border-b-[3px] px-3 py-2.5 first:pl-0 ${vue === v ? "border-accent font-semibold" : "border-transparent text-texte-2 hover:text-texte"}`}
                >
                  {t.vues[v]}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        <p className="flex items-baseline gap-2 border-b border-ligne bg-fond px-4 py-1.5 text-[13px] text-texte-2 lg:px-6">
          <span className="rounded-sm bg-attention-clair px-1.5 font-semibold text-attention">{t.prototype}</span>
          <span>{t.prototypeTexte}</span>
        </p>
      </header>

      <main ref={contenu} className={`fond-motif min-h-0 flex-1 ${vue === "assistant" ? "lg:overflow-hidden" : "lg:overflow-y-auto"}`}>
        {vue === "demarches" && <Annuaire demarches={catalogue} langue={langue} onOuvrir={ouvrir} />}

        {vue === "sources" && <ListeSources documents={documents} stats={stats} erreur={erreurDocuments} langue={langue} />}

        {vue === "donnees" && (
          <div className="max-w-[1180px] px-4 py-6 lg:px-6">
            <Notice notice={notice} erreur={erreurNotice} langue={langue} consent={consent} enAttente={enAttente} onAccepter={accepter} onRefuser={refuser} onRetirer={retirerConsentement} />
          </div>
        )}

        {vue === "assistant" && (
          <div className="lg:grid lg:h-full lg:grid-cols-[360px_minmax(0,1fr)]">
            <section aria-label={t.echanges} className="flex flex-col border-b border-ligne bg-fond lg:h-full lg:min-h-0 lg:border-b-0 lg:border-r">
              <div className="flex items-center justify-between border-b border-ligne px-4 py-2">
                <h2 className="text-sm font-semibold">{t.echanges}</h2>
                {messages.length > 0 && (
                  <button onClick={effacer} disabled={chargement} className="text-sm text-accent underline underline-offset-2 disabled:opacity-50">
                    {t.effacer}
                  </button>
                )}
              </div>
              <div className="lg:min-h-0 lg:flex-1 lg:overflow-y-auto" aria-live="polite">
                {messages.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-texte-2">{t.aucunEchange}</p>
                ) : (
                  <ol className="divide-y divide-ligne">
                    {messages.map((m, i) =>
                      m.role === "user" ? (
                        <li key={i} className="px-4 pb-3 pt-3">
                          <p className="mb-2 whitespace-pre-wrap font-semibold">{m.content}</p>
                          {messages[i + 1] && (
                            <ReponseDansLeFil message={messages[i + 1]} index={i + 1} selection={selection} occupe={chargement} consent={consent} t={t} onSelection={setSelection} onOption={envoyer} />
                          )}
                        </li>
                      ) : null,
                    )}
                  </ol>
                )}
                <div ref={finDuFil} />
              </div>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  envoyer(saisie);
                }}
                className="fixed inset-x-0 bottom-0 z-20 flex gap-2 border-t border-ligne bg-surface p-3 lg:static"
              >
                <input
                  type="text"
                  value={saisie}
                  maxLength={1000}
                  disabled={!consent}
                  onChange={(e) => setSaisie(e.target.value)}
                  placeholder={consent ? t.placeholder : t.placeholderBloque}
                  aria-label={t.champ}
                  className="min-w-0 flex-1 rounded border border-ligne-forte bg-surface px-2.5 py-2 placeholder:text-texte-2 disabled:cursor-not-allowed disabled:bg-fond"
                />
                <button
                  type="submit"
                  disabled={!consent || chargement || !saisie.trim()}
                  className="shrink-0 rounded bg-accent px-3.5 py-2 font-semibold text-white hover:bg-accent-fonce disabled:cursor-not-allowed disabled:bg-[#e3e6ea] disabled:text-[#55606d]"
                >
                  {t.envoyer}
                </button>
              </form>
            </section>

            <section ref={panneau} aria-label={t.fiche} className="scroll-mt-0 pb-20 lg:h-full lg:overflow-y-auto lg:pb-0">
              {!consent ? (
                <div className="px-4 py-6 lg:px-8">
                  <Notice notice={notice} erreur={erreurNotice} langue={langue} consent={consent} enAttente={enAttente} onAccepter={accepter} onRefuser={refuser} onRetirer={retirerConsentement} />
                </div>
              ) : ficheOuverte ? (
                <Fiche key={selection} message={ficheOuverte} langue={langue} consent={consent} />
              ) : (
                <div className="max-w-[720px] px-4 py-6 lg:px-8">
                  <h1 className="text-[26px] font-bold leading-tight">{t.assistantTitre}</h1>
                  <p className="mt-2 text-texte-2">{t.assistantTexte}</p>
                  <h2 className="mt-6 border-b-2 border-texte pb-1.5 text-[17px] font-bold">{t.exemplesTitre}</h2>
                  <ul className="divide-y divide-ligne">
                    {t.exemples.map((exemple) => (
                      <li key={exemple}>
                        <button
                          disabled={chargement}
                          onClick={() => envoyer(exemple)}
                          className="block w-full py-2 text-left font-medium text-accent underline-offset-2 hover:underline disabled:opacity-50"
                        >
                          {exemple}
                        </button>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-5 text-sm text-texte-2">
                    <Etat ton="ok">{t.accordDonne}</Etat>
                    <span aria-hidden="true"> · </span>
                    <button onClick={() => setVue("donnees")} className="text-accent underline underline-offset-2">
                      {t.vues.donnees}
                    </button>
                  </p>
                </div>
              )}
            </section>
          </div>
        )}

        {vue !== "assistant" && <footer className="max-w-[1180px] px-4 pb-6 pt-2 text-[13px] text-texte-2 lg:px-6">{t.pied}</footer>}
      </main>
    </div>
  );
}
