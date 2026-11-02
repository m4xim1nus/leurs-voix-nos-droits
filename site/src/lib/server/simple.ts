// Résumé « en mots simples » d'un texte qualifié (cycle Facile à lire, docs/CONCEPTION.md).
//
// Il n'est affiché que si son empreinte correspond encore à la fiche : une fiche changée depuis sa
// relecture le rend « à revoir », et le site ne le montre plus. Même calcul que le pipeline
// (`editorial.empreinte_simple`) et l'admin (`empreinteSimple`), vérifié sur la fixture partagée
// pipeline/tests/fixtures/editorial_simple.json.

export interface Fiche {
  titre: string;
  resume: string;
  droits: { code: string }[];
  conseil_constitutionnel: string;
  resume_simple?: { texte: string; empreinte: string };
}

/** Titre, résumé, codes des droits touchés et décision du Conseil, en FNV-1a sur 64 bits. */
export function empreinteSimple(t: Fiche): string {
  const base = [
    t.titre ?? '',
    t.resume ?? '',
    (t.droits ?? []).map((d) => d.code).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0)),
    t.conseil_constitutionnel ?? ''
  ];
  let h = 0xcbf29ce484222325n;
  for (const o of new TextEncoder().encode(JSON.stringify(base)))
    h = ((h ^ BigInt(o)) * 0x100000001b3n) & 0xffffffffffffffffn;
  return h.toString(16).padStart(16, '0');
}

/** Les phrases du résumé simple à afficher, ou null s'il n'y en a pas ou s'il est à revoir. */
export function phrasesSimples(t: Fiche): string[] | null {
  const r = t.resume_simple;
  if (!r?.texte || r.empreinte !== empreinteSimple(t)) return null;
  return r.texte.split('\n').filter(Boolean);
}
