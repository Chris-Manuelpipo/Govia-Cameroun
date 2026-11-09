/**
 * Copie un texte dans le presse-papiers. L'API moderne n'existe qu'en HTTPS ou sur localhost :
 * un poste servi en HTTP simple (cybercafé, réseau local) passe par le repli historique.
 */
export async function copierTexte(texte: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(texte);
      return true;
    }
  } catch {
    // Permission refusée : on tente le repli.
  }
  const actif = document.activeElement as HTMLElement | null;
  try {
    const zone = document.createElement("textarea");
    zone.value = texte;
    zone.setAttribute("readonly", "");
    zone.style.position = "fixed";
    zone.style.opacity = "0";
    document.body.appendChild(zone);
    zone.select();
    const copie = document.execCommand("copy");
    document.body.removeChild(zone);
    return copie;
  } catch {
    return false;
  } finally {
    // La zone temporaire a pris le focus : on le rend au bouton qui a demandé la copie.
    actif?.focus?.();
  }
}
