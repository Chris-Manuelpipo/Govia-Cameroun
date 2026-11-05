#!/usr/bin/env python3
"""
GOVIA Cameroun — Capture vidéo de démonstration
Navigue dans l'app, pose des questions représentatives, capture vidéo + screenshots.
"""
import asyncio
import os
import subprocess
import sys
from playwright.async_api import async_playwright

APP_URL = "http://localhost:3000"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo")
os.makedirs(OUT_DIR, exist_ok=True)

# Questions représentatives : pièces d'identité, autres démarches, lacune, refus.
SCENARIOS = [
    {"q": "Je veux renouveler ma carte", "label": "ambiguite"},
    {"q": "Je veux renouveler ma CNI, je l'ai perdue", "label": "cni"},
    {"q": "Je veux créer une société", "label": "societe"},
    {"q": "Je veux un permis de construire", "label": "construire"},
    {"q": "Je veux obtenir mon permis de conduire", "label": "lacune"},
    {"q": "Comment faire un faux passeport ?", "label": "refus"},
]
# Le LLM local peut être lent : on attend la fin de la réponse, dans cette limite.
ATTENTE_MAX_MS = 200_000

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=OUT_DIR,
            record_video_size={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        # Navigate to app
        await page.goto(APP_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Accept consent
        consent_btn = page.locator("button:has-text(\"j'accepte\")")
        if await consent_btn.count() > 0:
            await consent_btn.click()
            await page.wait_for_timeout(1000)

        # Demo flow
        for i, sc in enumerate(SCENARIOS):
            print(f"[{i+1}/{len(SCENARIOS)}] {sc['label']}")

            # Type question
            input_box = page.locator("input[placeholder*='Posez']")
            await input_box.click()
            await input_box.fill(sc["q"])
            await page.wait_for_timeout(300)

            # Send
            send_btn = page.locator("button:has-text('Envoyer')")
            await send_btn.click()

            # Attend la fin de la réponse : disparition de l'indicateur de frappe.
            await page.wait_for_function("document.querySelectorAll('.typing-dot').length === 0", timeout=ATTENTE_MAX_MS)
            await page.wait_for_timeout(1500)

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            # Take screenshot
            await page.screenshot(path=os.path.join(OUT_DIR, f"screenshot_{i+1}_{sc['label']}.png"), full_page=False)

        # Capture final state
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        await browser.close()
        print(f"✅ Capture terminée — vidéos et screenshots dans {OUT_DIR}")

asyncio.run(capture())

# Encode video from webm recordings
print("\n=== Encodage vidéo ===")
ffmpeg = subprocess.run(
    ["python3", "-c", "import static_ffmpeg; static_ffmpeg.add_paths(); import shutil; print(shutil.which('ffmpeg'))"],
    capture_output=True, text=True, check=True
)
ffmpeg_path = ffmpeg.stdout.strip()
print(f"FFmpeg: {ffmpeg_path}")

# Concat all webm recordings
webm_files = sorted([f for f in os.listdir(OUT_DIR) if f.endswith(".webm")])
if webm_files:
    concat_list = os.path.join(OUT_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for wf in webm_files:
            f.write(f"file '{os.path.join(OUT_DIR, wf)}'\n")

    final_video = os.path.join(OUT_DIR, "GOVIA_Demo_Cameroun.mp4")
    cmd = [
        ffmpeg_path, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-vf", "scale=1280:800",
        final_video
    ]
    print(f"Encodage: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        size = os.path.getsize(final_video)
        print(f"✅ Vidéo générée: {final_video} ({size/1024/1024:.1f} MB)")
    else:
        print(f"❌ Erreur encodage: {result.stderr[-500:]}")
        # Fallback: keep webm files
        print("WebM files conservés:")
        for wf in webm_files:
            print(f"  {wf}")
else:
    print("Aucun fichier webm trouvé")
