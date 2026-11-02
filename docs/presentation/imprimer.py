"""Refait leurs-voix-nos-droits.pdf depuis le deck Bento, en PDF vectoriel (texte sélectionnable).

Usage, depuis la racine du dépôt : uv run --with playwright python -I docs/presentation/imprimer.py
Il faut un Chromium pour Playwright : `uv run --with playwright playwright install chromium` la première fois.

Le script ouvre le deck, déclenche son bouton « Export PDF (print) » en neutralisant la boîte d'impression, puis
fait imprimer la page par Chromium. Les captures d'écran de l'export manuel donnaient un texte non sélectionnable.
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

ICI = Path(__file__).resolve().parent
DECK = ICI / "leurs-voix-nos-droits.bento.html"
PDF = ICI / "leurs-voix-nos-droits.pdf"


async def main() -> None:
    async with async_playwright() as p:
        navigateur = await p.chromium.launch()
        page = await navigateur.new_page(viewport={"width": 1600, "height": 900})
        await page.goto(DECK.as_uri())
        await page.wait_for_timeout(4000)  # l'application monte le deck
        await page.evaluate("() => { window.print = () => { window.__imprime = true; }; }")
        await page.click('[title="Export PDF (print)"]')
        await page.wait_for_timeout(6000)  # mise en page d'impression, images et polices
        if not await page.evaluate("() => !!window.__imprime"):
            raise SystemExit("le bouton « Export PDF (print) » n'a pas lancé l'impression : Bento a changé ?")
        await page.emulate_media(media="print")
        await page.pdf(path=PDF, prefer_css_page_size=True, print_background=True)
        await navigateur.close()
    print(PDF)


asyncio.run(main())
