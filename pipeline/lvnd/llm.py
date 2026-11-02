"""Usage du LLM (ROADMAP, cycle Pré-qualification, item 2) : réglages et journal dans D1, clé chiffrée,
coût estimé, plafond.

L'admin écrit les réglages (page « LLM », admin/src/lib/server/llm.ts) ; ce module les lit avant tout
appel et journalise chacun dans `llm_appels`. Les règles sont celles de l'admin : interrupteur coupé,
secret ou clé absents, plafond du mois atteint → aucun appel. Un appel n'est ouvert que s'il reste au
moins `RESERVE_USD` sous le plafond : le coût d'une requête n'est connu qu'après coup.
"""

import base64
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import sync_admin

# Dollars par million de jetons (https://platform.claude.com/docs/en/about-claude/pricing, 02/11/2026).
TARIFS = {
    "claude-opus-5-5": {"entree": 4.0, "cache_ecrit": 5.0, "cache_ecrit_1h": 8.0, "cache_lu": 0.20, "sortie": 20.0},
    "claude-sonnet-5-5": {"entree": 2.0, "cache_ecrit": 2.5, "cache_ecrit_1h": 4.0, "cache_lu": 0.10, "sortie": 10.0},
}
MODELES = tuple(TARIFS)
MODELE_DEFAUT = "claude-opus-5-5"
PLAFOND_DEFAUT = 20.0
RECHERCHE_USD = 0.01  # 10 $ les 1 000 recherches web ; la lecture d'une page (web_fetch) ne coûte que ses jetons
RESERVE_USD = 1.0

DONNEES_ASSOCIEES = b"lvnd-llm-cle"


def dechiffrer(secret: str, valeur: str) -> str:
    """Clé chiffrée par l'admin : « v1: » + base64(nonce de 12 octets ‖ chiffré ‖ étiquette), AES-GCM 256,
    clé de chiffrement = SHA-256 du secret LLM_CHIFFREMENT."""
    if not valeur.startswith("v1:"):
        raise ValueError("format de clé chiffrée inconnu")
    tout = base64.b64decode(valeur[3:])
    cle = hashlib.sha256(secret.encode()).digest()
    return AESGCM(cle).decrypt(tout[:12], tout[12:], DONNEES_ASSOCIEES).decode()


def cout(modele: str, usage) -> float:
    """Coût estimé d'une requête, d'après son `usage` (objet du SDK ou dict). Modèle inconnu : tarif
    du modèle par défaut, le plus cher des deux, pour ne pas sous-estimer."""
    u = usage if isinstance(usage, dict) else usage.model_dump()
    t = TARIFS.get(modele, TARIFS[MODELE_DEFAUT])
    ecrits = u.get("cache_creation_input_tokens") or 0
    detail = u.get("cache_creation") or {}
    ecrits_1h = detail.get("ephemeral_1h_input_tokens") or 0
    recherches = (u.get("server_tool_use") or {}).get("web_search_requests") or 0
    return ((u.get("input_tokens") or 0) * t["entree"]
            + (ecrits - ecrits_1h) * t["cache_ecrit"] + ecrits_1h * t["cache_ecrit_1h"]
            + (u.get("cache_read_input_tokens") or 0) * t["cache_lu"]
            + (u.get("output_tokens") or 0) * t["sortie"]) / 1e6 + recherches * RECHERCHE_USD


class D1:
    """Accès à la base de l'admin par `wrangler d1 execute` (comme `lvnd sync-admin`)."""

    def __init__(self, cible: str, admin: Path):
        self.cible, self.admin = cible, admin

    def lire(self, sql: str) -> list[dict]:
        return sync_admin._requete(self.admin, self.cible, sql)

    def ecrire(self, sql: str) -> None:
        sync_admin._requete(self.admin, self.cible, sql)


@dataclass
class Reglages:
    actif: bool = False
    plafond_usd: float = PLAFOND_DEFAUT
    modele: str = MODELE_DEFAUT
    cle_chiffree: str | None = None


def _json(v: str | None):
    try:
        return json.loads(v) if v is not None else None
    except ValueError:
        return None


def lire_reglages(d1) -> Reglages:
    par = {r["cle"]: _json(r["valeur"]) for r in d1.lire("SELECT cle, valeur FROM llm_reglages")}
    plafond, modele, cle = par.get("plafond_usd"), par.get("modele"), par.get("cle_api")
    return Reglages(
        actif=par.get("actif") is True,
        plafond_usd=float(plafond) if isinstance(plafond, (int, float)) and plafond >= 0 else PLAFOND_DEFAUT,
        modele=modele if modele in MODELES else MODELE_DEFAUT,
        cle_chiffree=cle.get("chiffre") if isinstance(cle, dict) else None,
    )


def depense_du_mois(d1, maintenant: str) -> float:
    r = d1.lire(f"SELECT COALESCE(SUM(cout_usd), 0) AS s FROM llm_appels WHERE substr(date, 1, 7) = '{maintenant[:7]}'")
    return float(r[0]["s"]) if r else 0.0


def etat(r: Reglages, depense: float, secret: bool) -> str:
    """Même règle que l'admin (lib/server/llm.ts, `etat`)."""
    if not r.actif:
        return "coupe"
    if not secret:
        return "sans-secret"
    if not r.cle_chiffree:
        return "sans-cle"
    if depense >= r.plafond_usd:
        return "plafond"
    return "en-service"


MOTIFS = {
    "coupe": "usage du LLM coupé dans l'admin",
    "sans-secret": "secret LLM_CHIFFREMENT absent",
    "sans-cle": "aucune clé enregistrée dans l'admin",
    "plafond": "plafond du mois atteint",
}


class Indisponible(Exception):
    """Aucun appel possible : interrupteur, secret, clé ou plafond. Jamais une erreur de la passe de données."""


def maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Session:
    """Appels d'une tâche : vérifie le plafond avant chaque requête, journalise chacune après.

    `client` : un client du SDK (créé depuis la clé déchiffrée si absent)."""

    d1: object
    tache: str
    client: object = None
    secret: str | None = field(default_factory=lambda: os.environ.get("LLM_CHIFFREMENT"))
    reglages: Reglages = None
    depense: float = 0.0
    appels: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.reglages = lire_reglages(self.d1)
        self.depense = depense_du_mois(self.d1, maintenant())
        e = etat(self.reglages, self.depense, bool(self.secret))
        if e != "en-service":
            raise Indisponible(MOTIFS[e])
        if self.client is None:
            import anthropic
            try:
                cle = dechiffrer(self.secret, self.reglages.cle_chiffree)
            except Exception as ex:  # secret différent de celui de l'admin : clé illisible
                raise Indisponible(f"clé illisible avec ce secret LLM_CHIFFREMENT ({type(ex).__name__})") from None
            self.client = anthropic.Anthropic(api_key=cle, max_retries=3, timeout=900)

    @property
    def modele(self) -> str:
        return self.reglages.modele

    def reste(self) -> float:
        return self.reglages.plafond_usd - self.depense

    def appeler(self, dossier: str | None, **params):
        """Une requête Messages (en flux, message final rendu). Lève `Indisponible` si le plafond est trop
        proche ; journalise l'appel, réussi ou non."""
        if self.reste() < RESERVE_USD:
            raise Indisponible(f"{MOTIFS['plafond']} ({self.depense:.2f} $ sur {self.reglages.plafond_usd:.2f} $, "
                               f"réserve de {RESERVE_USD:.2f} $ par appel)")
        try:
            with self.client.messages.stream(model=self.modele, **params) as flux:
                message = flux.get_final_message()
        except Exception as ex:
            self._journal(dossier, None, "erreur", f"{type(ex).__name__} : {str(ex)[:300]}")
            raise
        resultat = {"end_turn": "ok", "pause_turn": "pause", "refusal": "refus",
                    "max_tokens": "tronque"}.get(message.stop_reason, message.stop_reason or "?")
        detail = None
        if message.stop_reason == "refusal" and getattr(message, "stop_details", None):
            detail = f"refus : {message.stop_details.category}"
        self._journal(dossier, message.usage, resultat, detail)
        return message

    def _journal(self, dossier, usage, resultat: str, detail: str | None) -> None:
        u = usage.model_dump() if usage is not None else {}
        c = cout(self.modele, u) if u else 0.0
        self.depense += c
        ligne = {
            "date": maintenant(), "tache": self.tache, "dossier_an": dossier, "modele": self.modele,
            "jetons_entree": u.get("input_tokens") or 0, "jetons_sortie": u.get("output_tokens") or 0,
            "jetons_cache_lus": u.get("cache_read_input_tokens") or 0,
            "jetons_cache_ecrits": u.get("cache_creation_input_tokens") or 0,
            "recherches_web": (u.get("server_tool_use") or {}).get("web_search_requests") or 0,
            "cout_usd": round(c, 6), "resultat": resultat, "detail": detail,
        }
        self.appels.append(ligne)
        cols = tuple(ligne)
        self.d1.ecrire(sync_admin.inserts("llm_appels", cols, [ligne])[0])
