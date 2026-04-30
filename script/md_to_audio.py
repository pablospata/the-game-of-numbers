"""
Convertir capítulos .md a audio .mp3 usando edge-tts (Microsoft Edge Neural TTS)
Uso:
    python md_to_audio.py                        # Convierte TODOS los capítulos
    python md_to_audio.py --file <archivo.md>    # Convierte un solo archivo
    python md_to_audio.py --voice es-MX-DaliaNeural  # Cambia la voz
    python md_to_audio.py --list-voices          # Lista voces disponibles en español
"""

import asyncio
import argparse
import re
import os
import io
import sys

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts no está instalado. Instalalo con:")
    print("   pip install edge-tts")
    sys.exit(1)


# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ES_DIR = os.path.join(BASE_DIR, "es")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

# Voz por defecto (argentina)
DEFAULT_VOICE = "es-AR-ElenaNeural"


def strip_markdown(text: str) -> str:
    """Limpia formato Markdown para que la lectura sea más natural."""
    # Quitar headers (#)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Quitar bold/italic
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)
    # Quitar links [texto](url)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # Quitar imágenes ![alt](url)
    text = re.sub(r"!\[.*?\]\(.+?\)", "", text)
    # Quitar blockquotes >
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Quitar listas - o *
    text = re.sub(r"^[\-\*]\s+", "", text, flags=re.MULTILINE)
    # Quitar listas numeradas
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    # Quitar líneas horizontales
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    # Limpiar líneas vacías múltiples
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def convert_file(md_path: str, output_path: str, voice: str) -> bool:
    """Convierte un archivo .md a .mp3"""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        clean_text = strip_markdown(content)

        if not clean_text:
            print(f"  ⚠️  Archivo vacío después de limpiar: {os.path.basename(md_path)}")
            return False

        print(f"  🔊 Generando audio ({len(clean_text)} caracteres)...")

        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(output_path)

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✅ {os.path.basename(output_path)} ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def list_spanish_voices():
    """Lista todas las voces disponibles en español."""
    voices = await edge_tts.list_voices()
    spanish = [v for v in voices if v["Locale"].startswith("es-")]

    print("\n🎤 Voces disponibles en español:\n")
    print(f"  {'Nombre':<30} {'Género':<10} {'Locale':<8}")
    print(f"  {'─' * 30} {'─' * 10} {'─' * 8}")

    for v in sorted(spanish, key=lambda x: x["Locale"]):
        print(f"  {v['ShortName']:<30} {v['Gender']:<10} {v['Locale']:<8}")

    print(f"\n  Total: {len(spanish)} voces")


async def main():
    parser = argparse.ArgumentParser(description="Convertir capítulos .md a audio .mp3")
    parser.add_argument("--file", "-f", help="Archivo .md específico a convertir")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE, help=f"Voz a usar (default: {DEFAULT_VOICE})")
    parser.add_argument("--list-voices", "-l", action="store_true", help="Listar voces en español disponibles")
    parser.add_argument("--output-dir", "-o", default=AUDIO_DIR, help=f"Directorio de salida (default: {AUDIO_DIR})")
    args = parser.parse_args()

    if args.list_voices:
        await list_spanish_voices()
        return

    # Crear directorio de salida
    os.makedirs(args.output_dir, exist_ok=True)

    if args.file:
        # Convertir un solo archivo
        md_path = args.file
        if not os.path.isabs(md_path):
            # Try relative to CWD first, then ES_DIR
            cwd_path = os.path.join(os.getcwd(), md_path)
            es_path = os.path.join(ES_DIR, md_path)
            if os.path.exists(cwd_path):
                md_path = cwd_path
            elif os.path.exists(es_path):
                md_path = es_path

        if not os.path.exists(md_path):
            print(f"❌ No se encontró: {md_path}")
            return

        basename = os.path.splitext(os.path.basename(md_path))[0]
        output_path = os.path.join(args.output_dir, f"{basename}.mp3")

        print(f"\n📖 Convirtiendo: {os.path.basename(md_path)}")
        print(f"🎤 Voz: {args.voice}\n")
        await convert_file(md_path, output_path, args.voice)

    else:
        # Convertir todos los archivos
        md_files = sorted([
            f for f in os.listdir(ES_DIR)
            if f.endswith(".md") and f != "libro-completo.md"
        ])

        print(f"\n📚 Convirtiendo {len(md_files)} capítulos a audio")
        print(f"🎤 Voz: {args.voice}")
        print(f"📁 Salida: {args.output_dir}\n")

        success = 0
        for i, filename in enumerate(md_files, 1):
            md_path = os.path.join(ES_DIR, filename)
            basename = os.path.splitext(filename)[0]
            output_path = os.path.join(args.output_dir, f"{basename}.mp3")

            print(f"[{i}/{len(md_files)}] {filename}")
            if await convert_file(md_path, output_path, args.voice):
                success += 1

        print(f"\n🎉 Listo! {success}/{len(md_files)} archivos convertidos")
        print(f"📁 Audio en: {args.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
