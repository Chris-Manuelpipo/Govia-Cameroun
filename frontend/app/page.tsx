"use client";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Langue, TEXTES } from "./i18n";

interface Citation {
  id: string;
  article: string;
  texte: string;
  titre: string;
  source_url: string;
  type_source: "texte_officiel" | "reproduction" | "portail_institutionnel";
  statut_verification: string;
  note: string;
}

interface Controle {
  nom: string;
  resultat: "ok" | "reserve" | "echec";
  detail: string;
}

interface Audit {
  verdict: "conforme" | "partiel" | "non_conforme";
  controles: Controle[];
  gaps: string[];
}

interface Formulaire {
  procedure_id: string;
  plateforme: string;
  champs: { nom: string; valeur: string }[];
}

interface Option {
  libelle: string;
  message: string;
}

interface Message {
  role: "user" | "agent";
  content: string;
  type?: string;
  procedure?: string | null;
  statut?: "couvert" | "partiel" | "lacune" | null;
  options?: Option[];
  citations?: Citation[];
  audit?: Audit;
  formulaire?: Formulaire | null;
  chargement?: boolean;
}

type Notice = Record<string, string>;

const RUBRIQUES = ["responsable", "finalite", "donnees", "destinataires", "conservation", "transfert", "droits", "limites"] as const;

/** Affiche le gras et les listes produits par l'agent, sans jamais injecter de HTML. */
function TexteAgent({ texte }: { texte: string }) {
  return (
    <div className="text-sm leading-relaxed space-y-1">
      {texte.split("\n").map((ligne, i) => {
        if (!ligne.trim()) return <div key={i} className="h-2" />;
        const liste = /^(\s*-\s|\s*\d+\.\s)/.test(ligne);
        const morceaux = ligne.split(/(\*\*[^*]+\*\*)/g).map((m, j) =>
          m.startsWith("**") && m.endsWith("**") ? <strong key={j}>{m.slice(2, -2)}</strong> : <span key={j}>{m}</span>,
        );
        return (
          <p key={i} className={liste ? "pl-3" : ""}>
            {morceaux}
          </p>
        );
      })}
    </div>
  );
}

function FormulaireCitoyen({ initial, langue, consent }: { initial: Formulaire; langue: Langue; consent: boolean }) {
  const t = TEXTES[langue];
  const [champs, setChamps] = useState(initial.champs);
  const [ouvert, setOuvert] = useState(false);
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

  if (!ouvert) {
    return (
      <button
        onClick={() => setOuvert(true)}
        className="mt-3 text-xs font-bold text-[#0369A1] border border-[#0369A1] rounded-lg px-3 py-1.5 hover:bg-[#E0F2FE]"
      >
        {t.formulaire}
      </button>
    );
  }

  return (
    <div className="mt-3 border border-[#E2E8F0] rounded-xl p-3 bg-[#F8FAFC]">
      <p className="text-xs text-[#475569] mb-2">{t.formulaireIntro(initial.plateforme)}</p>
      <div className="grid sm:grid-cols-2 gap-2">
        {champs.map((c) => (
          <label key={c.nom} className="text-xs text-[#475569]">
            {t.champs[c.nom] || c.nom}
            <input
              value={c.valeur}
              onChange={(e) => modifier(c.nom, e.target.value)}
              className="mt-0.5 w-full bg-white border border-[#E2E8F0] rounded-lg px-2 py-1.5 text-sm text-[#020617]"
            />
          </label>
        ))}
      </div>
      <p className="text-[11px] text-[#92400E] mt-2">{t.lectureAvertissement}</p>
      {erreur && <p role="alert" className="text-xs text-[#DC2626] mt-1">{erreur}</p>}
      <div className="flex flex-wrap gap-2 mt-2">
        <label className="text-xs font-semibold text-[#0369A1] border border-[#E2E8F0] bg-white rounded-lg px-3 py-1.5 cursor-pointer hover:border-[#0369A1]">
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
        <button onClick={copier} className="text-xs font-semibold text-white bg-[#0F172A] rounded-lg px-3 py-1.5 hover:bg-[#0369A1]">
          {copie ? t.copie : t.copier}
        </button>
      </div>
    </div>
  );
}

export default function Home() {
  const [langue, setLangue] = useState<Langue>("FR");
  const [messages, setMessages] = useState<Message[]>([]);
  const [saisie, setSaisie] = useState("");
  const [chargement, setChargement] = useState(false);
  const [consent, setConsent] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [erreurNotice, setErreurNotice] = useState(false);
  const fin = useRef<HTMLDivElement>(null);
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
    fin.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chargement]);

  async function envoyer(texte: string) {
    if (!consent || chargement || !texte.trim()) return;

    // L'historique permet de répondre à une question de précision de l'agent.
    const historique = messages
      .filter((m) => !m.chargement)
      .slice(-8)
      .map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.content.slice(0, 3900) }));

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
          consentement: consent,
          language: langue,
        }),
      });
      const corps = await reponse.json();
      if (!reponse.ok) {
        const detail = typeof corps.detail === "string" ? corps.detail : t.erreurService;
        remplacer({ role: "agent", content: `⚠️ ${detail}` });
        return;
      }
      remplacer({
        role: "agent",
        content: corps.agent.reponse,
        type: corps.agent.type_reponse,
        procedure: corps.agent.procedure_identifiee,
        statut: corps.agent.statut_demarche,
        options: corps.agent.options,
        citations: corps.agent.citations,
        audit: corps.audit,
        formulaire: corps.agent.formulaire_prerempli,
      });
    } catch {
      remplacer({ role: "agent", content: `⚠️ ${t.erreurConnexion}` });
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gradient-to-r from-[#0F172A] to-[#0F3D70] text-white px-6 py-3 shadow-lg">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#14598C] to-[#0F172A] flex items-center justify-center shadow-md">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" aria-hidden="true">
                <path d="M12 3 L20 6 V12 C20 16 16.5 19 12 21 C7.5 19 4 16 4 12 V6 Z" />
                <path d="M9 11 L9 16 L13 17.5" stroke="#7DD3FC" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="15" cy="8" r="1.5" fill="#FBBF24" stroke="none" />
              </svg>
            </div>
            <div>
              <div className="text-lg font-bold tracking-tight">GOVIA</div>
              <div className="text-[10px] tracking-[2px] text-[#93C5FD] uppercase">Cameroun</div>
            </div>
          </div>
          <div role="group" aria-label="Langue / Language" className="flex rounded-full border border-[#3B82F6] overflow-hidden">
            {(["FR", "EN"] as Langue[]).map((l) => (
              <button
                key={l}
                onClick={() => setLangue(l)}
                aria-pressed={langue === l}
                className={`text-xs font-semibold px-3 py-1.5 transition-all ${langue === l ? "bg-white text-[#0F172A]" : "text-[#BFDBFE] hover:bg-white/10"}`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
      </header>

      <AnimatePresence>
        {!consent && (
          <motion.section
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            aria-label={notice?.titre}
            className="bg-[#FEF9E7] border border-[#FBBF24] rounded-xl mx-4 mt-3 px-5 py-3 max-w-3xl md:mx-auto w-[calc(100%-2rem)]"
          >
            {erreurNotice && <p role="alert" className="text-sm text-[#92400E]">{t.consentementErreur}</p>}
            {!notice && !erreurNotice && <p className="text-sm text-[#92400E]">{t.consentementChargement}</p>}
            {notice && (
              <>
                <h2 className="text-sm font-bold text-[#92400E]">{notice.titre}</h2>
                <dl className="mt-1 space-y-1">
                  {RUBRIQUES.map((r) => (
                    <div key={r} className="text-xs text-[#92400E]">
                      <dt className="inline font-semibold">{t.rubriques[r]} : </dt>
                      <dd className="inline">{notice[r]}</dd>
                    </div>
                  ))}
                </dl>
                <button
                  onClick={() => setConsent(true)}
                  className="mt-2 bg-[#0F172A] text-white text-xs font-bold px-4 py-2 rounded-lg hover:bg-[#0369A1] transition-all"
                >
                  {notice.action}
                </button>
              </>
            )}
          </motion.section>
        )}
      </AnimatePresence>

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-4 flex flex-col gap-3">
        {consent && (
          <div className="flex items-center justify-end gap-2 text-[11px] text-[#475569]">
            <span>✓ {t.consentementAccord}</span>
            <button onClick={() => setConsent(false)} className="underline hover:text-[#DC2626]">
              {t.consentementRetirer}
            </button>
          </div>
        )}

        {messages.length === 0 && (
          <div className="bg-white border border-[#E2E8F0] rounded-2xl px-5 py-4 shadow-sm">
            <h1 className="text-base font-bold">{t.introTitre}</h1>
            <p className="text-sm text-[#475569] mt-1">{t.introTexte}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {t.exemples.map((exemple) => (
                <button
                  key={exemple}
                  disabled={!consent}
                  onClick={() => envoyer(exemple)}
                  className="text-xs text-[#0369A1] bg-[#E0F2FE] rounded-full px-3 py-1.5 hover:bg-[#BAE6FD] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exemple}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto space-y-4 min-h-[320px]" aria-live="polite">
          <AnimatePresence initial={false}>
            {messages.map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[90%] ${
                    m.role === "user"
                      ? "bg-[#0F172A] text-white rounded-2xl rounded-br-md px-4 py-3 shadow-md text-sm whitespace-pre-wrap"
                      : "bg-white border border-[#E2E8F0] rounded-2xl rounded-bl-md px-4 py-3 shadow-sm"
                  }`}
                >
                  {m.role === "user" ? (
                    m.content
                  ) : m.chargement ? (
                    <div className="flex items-center gap-1.5 py-2">
                      {[0, 200, 400].map((delai) => (
                        <span key={delai} className="typing-dot w-2 h-2 bg-[#475569] rounded-full" style={{ animationDelay: `${delai}ms` }} />
                      ))}
                    </div>
                  ) : (
                    <>
                      {(m.procedure || m.statut) && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {m.procedure && <span className="proc-badge text-xs font-bold px-2.5 py-1 rounded-full">{m.procedure}</span>}
                          {m.statut && (
                            <span
                              className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                                m.statut === "couvert" ? "audit-conforme" : m.statut === "partiel" ? "audit-partiel" : "audit-non-conforme"
                              }`}
                            >
                              {t.statuts[m.statut]}
                            </span>
                          )}
                        </div>
                      )}

                      <TexteAgent texte={m.content} />

                      {!!m.options?.length && (
                        <div className="flex flex-col items-start gap-1.5 mt-3">
                          {m.options.map((o) => (
                            <button
                              key={o.message}
                              disabled={chargement || !consent}
                              onClick={() => envoyer(o.message)}
                              className="text-xs font-semibold text-left text-[#0369A1] border border-[#0369A1] rounded-lg px-3 py-1.5 hover:bg-[#E0F2FE] disabled:opacity-50"
                            >
                              {o.libelle}
                            </button>
                          ))}
                        </div>
                      )}

                      {!!m.citations?.length && (
                        <details className="mt-3">
                          <summary className="text-xs font-bold text-[#92400E] cursor-pointer">{t.sources(m.citations.length)}</summary>
                          <div className="mt-2 flex flex-col gap-2">
                            {m.citations.map((c) => (
                              <a key={c.id} href={c.source_url} target="_blank" rel="noopener noreferrer" className="citation-card block px-3 py-2">
                                <div className="flex flex-wrap items-center gap-1.5 text-xs font-bold text-[#92400E]">
                                  <span>{c.article}</span>
                                  <span className="font-normal opacity-80">· {t.typesSource[c.type_source]}</span>
                                  <span className={`font-semibold px-1.5 rounded ${c.statut_verification === "verifie" ? "audit-conforme" : "audit-partiel"}`}>
                                    {c.statut_verification === "verifie" ? t.verifie : t.aVerifier}
                                  </span>
                                </div>
                                <div className="text-[11px] text-[#92400E] font-semibold mt-0.5">{c.titre}</div>
                                <div className="text-xs text-[#92400E] opacity-90 mt-0.5">{c.texte}</div>
                              </a>
                            ))}
                          </div>
                        </details>
                      )}

                      {m.formulaire && <FormulaireCitoyen initial={m.formulaire} langue={langue} consent={consent} />}

                      {m.audit && (
                        <details className="mt-3">
                          <summary className="flex items-center gap-2 cursor-pointer list-none">
                            <span
                              className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                                m.audit.verdict === "conforme" ? "audit-conforme" : m.audit.verdict === "partiel" ? "audit-partiel" : "audit-non-conforme"
                              }`}
                            >
                              {m.audit.verdict === "conforme" ? "✓" : m.audit.verdict === "partiel" ? "⚠" : "✗"} {t.verdicts[m.audit.verdict]}
                            </span>
                            <span className="text-[10px] text-[#475569] underline">
                              {t.auditeur} · {t.auditDetail}
                            </span>
                          </summary>
                          <ul className="mt-2 space-y-1 text-[11px] text-[#475569]">
                            {m.audit.controles.map((c, k) => (
                              <li key={k}>
                                {c.resultat === "ok" ? "✓" : c.resultat === "reserve" ? "⚠" : "✗"} <strong>{c.nom}</strong> : {c.detail}
                              </li>
                            ))}
                            {m.audit.gaps
                              .filter((g) => !m.audit?.controles.some((c) => c.detail === g))
                              .map((g, k) => (
                                <li key={`g${k}`}>⚠ {g}</li>
                              ))}
                          </ul>
                        </details>
                      )}
                    </>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={fin} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            envoyer(saisie);
          }}
          className="flex gap-2 pt-2"
        >
          <input
            type="text"
            value={saisie}
            maxLength={1000}
            disabled={!consent}
            onChange={(e) => setSaisie(e.target.value)}
            placeholder={consent ? t.placeholder : t.placeholderBloque}
            aria-label={t.placeholder}
            className="flex-1 bg-white border border-[#E2E8F0] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0369A1] focus:border-transparent transition-all shadow-sm disabled:bg-[#F1F5F9]"
          />
          <button
            type="submit"
            disabled={!consent || chargement || !saisie.trim()}
            className="bg-[#0F172A] text-white text-sm font-bold px-5 rounded-xl hover:bg-[#0369A1] disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            {chargement ? "..." : t.envoyer}
          </button>
        </form>
      </main>

      <footer className="text-center text-[10px] text-[#475569] py-3 px-4">{t.pied}</footer>
    </div>
  );
}
