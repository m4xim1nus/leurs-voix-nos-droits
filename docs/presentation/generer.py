#!/usr/bin/env python3
"""Reporte les chiffres du jour dans presentation.html, écrit presentation-a-imprimer.html et, si Chromium est là, le PDF.

Usage : python3 docs/presentation/generer.py [chemin de chromium]
Sans Chromium : ouvrir presentation-a-imprimer.html dans un navigateur, Imprimer, Enregistrer en PDF (voir README.md).
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).parent
DATA = ICI.parents[1] / "data"
ed = json.loads((DATA / "editorial.json").read_text())
meta = json.loads((DATA / "export/meta.json").read_text())
compter = lambda f: sum(1 for _ in csv.DictReader(open(DATA / "export" / f)))
milliers = lambda n: f"{n:,}".replace(",", " ")  # espace fine insécable
a, m, j = meta["genere_le"][:10].split("-")
page = (ICI / "presentation.html").read_text()
for cle, val in {"@QUALIFIES@": len(ed["textes"]), "@ECARTES@": len(ed["ecartes"]),
                 "@SCRUTINS@": milliers(compter("scrutins.csv") + compter("senat/scrutins.csv")), "@DATE@": f"{j}/{m}/{a}"}.items():
    page = page.replace(cle, str(val))
sortie = ICI / "presentation-a-imprimer.html"
sortie.write_text(page)
if len(sys.argv) > 1:
    subprocess.run([sys.argv[1], "--headless", "--no-pdf-header-footer", "--no-sandbox", "--virtual-time-budget=4000",
                    f"--print-to-pdf={ICI / 'leurs-voix-nos-droits.pdf'}", sortie.as_uri()], check=True)
    sortie.unlink()
