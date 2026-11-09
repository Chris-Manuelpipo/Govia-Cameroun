"use client";
import { useEffect, useRef, useState } from "react";
import { Annuaire } from "./components/Annuaire";
import { Assistant, Ouverture } from "./components/Assistant";
import { Donnees } from "./components/Donnees";
import { EnTete } from "./components/EnTete";
import { ListeSources } from "./components/ListeSources";
import { Navigation } from "./components/Navigation";
import { Langue, TEXTES } from "./i18n";
import { panneauDe } from "./lib/confiance";
import { DemarcheCatalogue, DocumentSource, Message, Notice as TypeNotice, Stats, Vue } from "./types";

export default function Home() {
  const [vue, setVue] = useState<Vue>("demarches");
  const [langue, setLangue] = useState<Langue>("FR");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selection, setSelection] = useState<number | null>(null);
  const [ouverture, setOuverture] = useState<Ouverture>({ n: 0, onglet: "demarche" });
  const [feuille, setFeuille] = useState(false);
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
  const [erreurCatalogue, setErreurCatalogue] = useState(false);
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
      .catch(() => {
        setCatalogue([]);
        setErreurCatalogue(true);
      });
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
    contenu.current?.scrollTo(0, 0);
    window.scrollTo(0, 0);
  }, [vue]);

  function effacer() {
    setMessages([]);
    setSelection(null);
    setFeuille(false);
    setOuverture({ n: 0, onglet: "demarche" });
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

  /** Ouvre le panneau d'une réponse déjà reçue, à la demande de l'utilisateur. */
  function ouvrirPanneau(index: number, onglet: "demarche" | "sources" = "demarche") {
    setSelection(index);
    setFeuille(true);
    setOuverture((o) => ({ n: o.n + 1, onglet }));
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
        procedureId: corps.agent.procedure_id,
        procedure: corps.agent.procedure_identifiee,
        statut: corps.agent.statut_demarche,
        mode: corps.agent.mode_generation,
        options: corps.agent.options,
        citations: corps.agent.citations,
        etapes: corps.agent.etapes,
        pieces: corps.agent.pieces_requises,
        audit: corps.audit,
        formulaire: corps.agent.formulaire_prerempli,
      };
      remplacer(message);
      // Fiche, précision requise ou aucun texte : la réponse s'ouvre dans le panneau. Sur grand écran le focus reste
      // dans le champ de saisie ; sur mobile le panneau remplace le fil et le focus l'y suit (voir Assistant).
      if (panneauDe(message)) {
        setSelection(indexReponse);
        setFeuille(true);
        setOuverture((o) => ({ n: o.n, onglet: "demarche" }));
      }
    } catch {
      remplacer({ role: "agent", erreur: true, content: t.erreurConnexion });
    } finally {
      setChargement(false);
    }
  }

  const surAssistant = vue === "assistant";

  return (
    <div className={`flex min-h-screen flex-col ${surAssistant ? "lg:h-screen lg:overflow-hidden" : ""}`}>
      <a
        href="#contenu"
        className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:bg-surface focus:px-4 focus:py-3 focus:font-semibold focus:text-titre focus:outline focus:outline-2 focus:outline-accent"
      >
        {t.allerAuContenu}
      </a>
      <EnTete langue={langue} t={t} onLangue={setLangue} />
      <Navigation vue={vue} t={t} onVue={setVue} />

      <main id="contenu" ref={contenu} tabIndex={-1} className={`fond-motif min-h-0 flex-1 focus:outline-none ${surAssistant ? "lg:overflow-hidden" : ""}`}>
        {vue === "demarches" && <Annuaire demarches={catalogue} erreur={erreurCatalogue} langue={langue} onOuvrir={ouvrir} />}

        {vue === "sources" && <ListeSources documents={documents} stats={stats} erreur={erreurDocuments} langue={langue} />}

        {vue === "donnees" && (
          <Donnees
            notice={notice}
            erreur={erreurNotice}
            langue={langue}
            consent={consent}
            enAttente={enAttente}
            stats={stats}
            documents={documents}
            catalogue={catalogue}
            onAccepter={accepter}
            onRefuser={refuser}
            onRetirer={retirerConsentement}
          />
        )}

        {surAssistant && (
          <Assistant
            langue={langue}
            t={t}
            messages={messages}
            selection={selection}
            ouverture={ouverture}
            feuille={feuille}
            saisie={saisie}
            chargement={chargement}
            consent={consent}
            catalogue={catalogue}
            notice={notice}
            erreurNotice={erreurNotice}
            enAttente={enAttente}
            onSaisie={setSaisie}
            onEnvoyer={envoyer}
            onEffacer={effacer}
            onOuvrir={ouvrirPanneau}
            onFermerFeuille={() => setFeuille(false)}
            onAccepter={accepter}
            onRefuser={refuser}
            onRetirer={retirerConsentement}
            onVue={setVue}
          />
        )}

        {!surAssistant && (
          <footer className="mx-auto max-w-[1280px] px-4 pb-8 pt-2 text-[13px] text-texte-2 lg:px-6">
            <p>{t.pied}</p>
          </footer>
        )}
      </main>
    </div>
  );
}
