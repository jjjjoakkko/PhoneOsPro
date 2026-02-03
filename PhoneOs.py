#!/usr/bin/env python3
"""
Phone OSINT Tool
Professional, Ethical, Single-file
"""

import re
import json
import csv
import argparse
import datetime
import sys
try:
    import phonenumbers
    from phonenumbers import (
        geocoder,
        carrier,
        timezone,
        number_type,
        PhoneNumberType,
    )
except ModuleNotFoundError:
    print("ERROR: módulo 'phonenumbers' no encontrado.")
    print()
    print("Asegúrate de activar el entorno virtual o ejecutar con el Python del entorno:")
    print("  PowerShell: .\\virtual\\Scripts\\Activate.ps1")
    print("  cmd:       .\\virtual\\Scripts\\activate.bat")
    print("  O ejecutar directamente:")
    print("  .\\virtual\\Scripts\\python.exe PhoneOs.py -h")
    sys.exit(1)

from colorama import Fore, Style, init
from tabulate import tabulate

# ---------------------------------------
# Init
# ---------------------------------------

init(autoreset=True)
LOG_FILE = "phone_osint.log"

# ---------------------------------------
# Visual helpers
# ---------------------------------------

def banner():
    print(Fore.CYAN + Style.BRIGHT + r"""
 ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗
 ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝
 ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  
 ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  
 ██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗
 ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
""")
    print(Fore.WHITE + "        Phone OSINT Tool — Ethical & Professional\n")


def section(title: str):
    print(Fore.CYAN + Style.BRIGHT + f"\n── {title} ──────────────────────────────")


def format_value(value, confidence):
    color = {
        "HIGH": Fore.GREEN,
        "MEDIUM": Fore.YELLOW,
        "LOW": Fore.MAGENTA,
        "NONE": Fore.RED
    }.get(confidence, Fore.WHITE)

    return color + f"{value} [{confidence}]"


# ---------------------------------------
# Logging
# ---------------------------------------

def log_event(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.utcnow().isoformat()}] {msg}\n")

# ---------------------------------------
# Input normalization
# ---------------------------------------

def normalize_input(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw)

    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]

    if not cleaned.startswith("+"):
        raise ValueError(
            "Formato inválido: se requiere código de país (E.164). "
            "Ejemplo: +5491155667788"
        )

    return cleaned

# ---------------------------------------
# Core analysis
# ---------------------------------------

def analyze_number(raw_number: str) -> dict:
    result = {
        "input_original": raw_number
    }

    try:
        normalized = normalize_input(raw_number)
        result["input_normalized"] = normalized
    except ValueError as e:
        result["error"] = str(e)
        return result

    try:
        num = phonenumbers.parse(normalized, None)
    except phonenumbers.NumberParseException:
        result["error"] = "Formato de número inválido"
        return result

    result["valid"] = phonenumbers.is_valid_number(num)
    if not result["valid"]:
        return result

    # Country
    country = geocoder.description_for_number(num, "es") or "UNKNOWN"
    result["country"] = {
        "value": country,
        "confidence": "HIGH" if country != "UNKNOWN" else "NONE"
    }

    # Region
    region = geocoder.description_for_number(num, "en") or "UNKNOWN"
    result["region"] = {
        "value": region,
        "confidence": "MEDIUM" if region != "UNKNOWN" else "NONE"
    }

    # Carrier
    car = carrier.name_for_number(num, "es")
    if car:
        result["carrier"] = {
            "value": car,
            "confidence": "MEDIUM"
        }
    else:
        result["carrier"] = {
            "value": "NOT DETERMINABLE",
            "confidence": "NONE"
        }

    # Line type
    result["line_type"] = {
        "value": PhoneNumberType.to_string(number_type(num)),
        "confidence": "MEDIUM"
    }

    # Timezones
    tzs = timezone.time_zones_for_number(num)
    result["timezones"] = {
        "value": ", ".join(tzs) if tzs else "NOT DETERMINABLE",
        "confidence": "HIGH" if tzs and len(tzs) == 1 else "MEDIUM"
    }

    # Formats
    result["formats"] = {
        "e164": phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164),
        "international": phonenumbers.format_number(
            num, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        ),
        "national": phonenumbers.format_number(
            num, phonenumbers.PhoneNumberFormat.NATIONAL
        ),
    }

    return result

# ---------------------------------------
# Output
# ---------------------------------------

def print_output(data: dict):
    banner()

    if "error" in data:
        section("ERROR")
        print(Fore.RED + "❌ " + data["error"])
        return

    section("INPUT")
    print(f"📥 Original     : {data['input_original']}")
    print(f"🧼 Normalizado  : {Fore.GREEN}{data['input_normalized']}")
    print(f"✔ Válido       : {Fore.GREEN}{data['valid']}")

    section("ANÁLISIS")
    print("🌍 País        :", format_value(**data["country"]))
    print("📍 Región      :", format_value(**data["region"]))
    print("📡 Operador    :", format_value(**data["carrier"]))
    print("📶 Tipo línea  :", format_value(**data["line_type"]))
    print("🕒 Zona horaria:", format_value(**data["timezones"]))

    section("FORMATOS")
    print("📞 E.164        :", data["formats"]["e164"])
    print("🌐 Internacional:", data["formats"]["international"])
    print("🏠 Nacional     :", data["formats"]["national"])

    section("NOTAS")
    print(Fore.YELLOW + "⚠️ La información mostrada se basa en estándares públicos.")
    print(Fore.YELLOW + "⚠️ No indica ubicación exacta ni operador actual garantizado.")

    print(Fore.CYAN + "\n──────────────────────────────────────\n")

# ---------------------------------------
# Main
# ---------------------------------------

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Phone OSINT Tool — Ethical & Professional"
    )

    parser.add_argument(
        "number",
        help="Número telefónico en formato internacional (E.164 recomendado)"
    )
    parser.add_argument("--json", action="store_true", help="Exportar a JSON")
    parser.add_argument("--csv", action="store_true", help="Exportar a CSV")

    args = parser.parse_args()

    data = analyze_number(args.number)
    print_output(data)

    log_event(f"Query: {args.number} | Valid: {data.get('valid')}")

    if args.json:
        with open("phone_osint_output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(Fore.GREEN + "✔ Exportado a phone_osint_output.json")

    if args.csv:
        with open("phone_osint_output.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for k, v in data.items():
                writer.writerow([k, v])
        print(Fore.GREEN + "✔ Exportado a phone_osint_output.csv")


if __name__ == "__main__":
    main()
