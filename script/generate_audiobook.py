"""
Genera el audiobook completo de "The Game of Numbers" dividido por secciones.

Secciones del libro:
  1. Prefacio e Introducción
  2. Primera Parte: Creencia (Capítulos 1-16)
  3. Segunda Parte: Conducta (Capítulos 17-45)
  4. Tercera Parte: Resistencia (Capítulos 46-71)
  5. Cuarta Parte: Habilidad (Capítulos 72-88)
  6. Coda y Material Complementario

Extras:
  7. Guía Práctica
  8. Checklist de Prospección
  9. Resumen Completo

Uso:
    python generate_audiobook.py
"""

import asyncio
import re
import os
import io
import sys
import time

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts no está instalado. Instalalo con: pip install edge-tts")
    sys.exit(1)

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ES_DIR = os.path.join(BASE_DIR, "es")
ANEXOS_DIR = os.path.join(BASE_DIR, "anexos")
RESUMEN_DIR = os.path.join(BASE_DIR, "resumen")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

VOICE = "es-MX-JorgeNeural"

# Definición de secciones del libro
SECTIONS = [
    {
        "name": "01-prefacio-e-introduccion",
        "title": "Prefacio e Introducción",
        "files": [
            "00-prefacio.md",
            "01-introduccion.md",
        ]
    },
    {
        "name": "02-parte-1-creencia",
        "title": "Primera Parte: Creencia (Capítulos 1-16)",
        "files": [f for f in sorted(os.listdir(os.path.join(BASE_DIR, "es")))
                  if f.endswith(".md") and f != "libro-completo.md"
                  and any(f.startswith(f"{i:02d}-") for i in range(2, 18))]
    },
    {
        "name": "03-parte-2-conducta",
        "title": "Segunda Parte: Conducta (Capítulos 17-45)",
        "files": [f for f in sorted(os.listdir(os.path.join(BASE_DIR, "es")))
                  if f.endswith(".md") and f != "libro-completo.md"
                  and any(f.startswith(f"{i:02d}-") for i in range(18, 47))]
    },
    {
        "name": "04-parte-3-resistencia",
        "title": "Tercera Parte: Resistencia (Capítulos 46-71)",
        "files": [f for f in sorted(os.listdir(os.path.join(BASE_DIR, "es")))
                  if f.endswith(".md") and f != "libro-completo.md"
                  and any(f.startswith(f"{i:02d}-") for i in range(47, 73))]
    },
    {
        "name": "05-parte-4-habilidad",
        "title": "Cuarta Parte: Habilidad (Capítulos 72-88)",
        "files": [f for f in sorted(os.listdir(os.path.join(BASE_DIR, "es")))
                  if f.endswith(".md") and f != "libro-completo.md"
                  and any(f.startswith(f"{i:02d}-") for i in range(73, 90))]
    },
    {
        "name": "06-coda-y-complementario",
        "title": "Coda y Material Complementario",
        "files": [f for f in sorted(os.listdir(os.path.join(BASE_DIR, "es")))
                  if f.endswith(".md") and f != "libro-completo.md"
                  and any(f.startswith(f"{i:02d}-") for i in range(90, 95))]
    },
]

# Archivos extra (no del libro principal)
EXTRAS = [
    {
        "name": "07-guia-practica",
        "title": "Guía Práctica: Destilado Accionable",
        "path": os.path.join(ANEXOS_DIR, "guia-practica.md"),
    },
    {
        "name": "08-checklist-prospeccion",
        "title": "Checklist de Prospección",
        "path": os.path.join(ANEXOS_DIR, "checklist-prospeccion.md"),
    },
    {
        "name": "09-resumen-completo",
        "title": "Resumen Completo",
        "path": os.path.join(RESUMEN_DIR, "resumen-completo.md"),
    },
]


def strip_markdown(text: str) -> str:
    """Limpia formato Markdown para lectura natural."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.+?\)", "", text)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_and_clean(filepath: str) -> str:
    """Lee un archivo .md y devuelve el texto limpio."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return strip_markdown(content)


async def generate_audio(text: str, output_path: str, voice: str) -> bool:
    """Genera un archivo de audio desde texto."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"    ❌ Error generando audio: {e}")
        return False


async def process_section(section: dict, voice: str) -> bool:
    """Procesa una sección del libro (múltiples archivos concatenados)."""
    output_path = os.path.join(AUDIO_DIR, f"{section['name']}.mp3")

    print(f"\n{'='*60}")
    print(f"📖 {section['title']}")
    print(f"   {len(section['files'])} archivos")

    # Concatenar contenido de todos los archivos de la sección
    all_text = []
    for filename in section["files"]:
        filepath = os.path.join(ES_DIR, filename)
        if os.path.exists(filepath):
            clean = read_and_clean(filepath)
            if clean:
                # Agregar una pausa natural entre capítulos
                all_text.append(clean)
        else:
            print(f"    ⚠️  No encontrado: {filename}")

    full_text = "\n\n...\n\n".join(all_text)  # "..." genera una pausa en TTS
    char_count = len(full_text)

    print(f"   📝 {char_count:,} caracteres totales")
    print(f"   🔊 Generando audio...")

    start = time.time()
    success = await generate_audio(full_text, output_path, voice)
    elapsed = time.time() - start

    if success:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ {section['name']}.mp3 ({size_mb:.1f} MB) [{elapsed:.0f}s]")
    return success


async def process_extra(extra: dict, voice: str) -> bool:
    """Procesa un archivo extra (guía, checklist, resumen)."""
    output_path = os.path.join(AUDIO_DIR, f"{extra['name']}.mp3")

    print(f"\n{'='*60}")
    print(f"📄 {extra['title']}")

    if not os.path.exists(extra["path"]):
        print(f"    ❌ No encontrado: {extra['path']}")
        return False

    clean_text = read_and_clean(extra["path"])
    char_count = len(clean_text)

    print(f"   📝 {char_count:,} caracteres")
    print(f"   🔊 Generando audio...")

    start = time.time()
    success = await generate_audio(clean_text, output_path, voice)
    elapsed = time.time() - start

    if success:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ {extra['name']}.mp3 ({size_mb:.1f} MB) [{elapsed:.0f}s]")
    return success


async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    print("🎧 GENERADOR DE AUDIOBOOK — The Game of Numbers")
    print(f"🎤 Voz: {VOICE}")
    print(f"📁 Salida: {AUDIO_DIR}")

    total_start = time.time()
    success_count = 0
    total_count = len(SECTIONS) + len(EXTRAS)

    # Procesar secciones del libro
    print("\n" + "="*60)
    print("📚 LIBRO — POR SECCIONES")
    print("="*60)

    for section in SECTIONS:
        if await process_section(section, VOICE):
            success_count += 1

    # Procesar extras
    print("\n" + "="*60)
    print("📎 MATERIAL EXTRA")
    print("="*60)

    for extra in EXTRAS:
        if await process_extra(extra, VOICE):
            success_count += 1

    # Resumen final
    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"🎉 COMPLETADO: {success_count}/{total_count} archivos generados")
    print(f"⏱️  Tiempo total: {total_elapsed/60:.1f} minutos")
    print(f"📁 Audios en: {AUDIO_DIR}")

    # Listar archivos generados
    print(f"\n📋 Archivos generados:")
    for f in sorted(os.listdir(AUDIO_DIR)):
        if f.endswith(".mp3"):
            size = os.path.getsize(os.path.join(AUDIO_DIR, f)) / (1024 * 1024)
            print(f"   🔊 {f} ({size:.1f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
