"""Position d'un groupe sur un scrutin (docs/METHODO.md, règle 12).

- position = majorité parmi les exprimés (pour contre contre) ;
- « abstention » (majoritairement abstentionniste) quand les abstentions dépassent à la fois les
  pour et les contre ;
- « partage » en cas d'égalité entre pour et contre, « absent » sans aucun votant ;
- cohésion = part des votants du groupe (pour, contre, abstention) qui ont voté comme la position.

datan.fr et leurs-votes.fr retiennent la majorité parmi les votants, abstention comprise : l'écart
touche environ 3 % des positions (docs/SOURCES.md).
"""


def position(pour: int, contre: int, abstention: int) -> tuple[str, float | None]:
    votants = pour + contre + abstention
    if not votants:
        return "absent", None
    if abstention > pour and abstention > contre:
        return "abstention", abstention / votants
    if pour == contre:
        return "partage", None
    return ("pour", pour / votants) if pour > contre else ("contre", contre / votants)


def positions(ventilations: list[dict]) -> list[dict]:
    out = []
    for v in ventilations:
        pos, coh = position(v["pour"], v["contre"], v["abstention"])
        out.append({**v, "position": pos, "cohesion": round(coh, 4) if coh is not None else None})
    return out
