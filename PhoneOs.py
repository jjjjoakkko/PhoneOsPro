#!/usr/bin/env python3
"""
Phone OSINT Tool — Pro Edition
Enhanced with: batch processing, caching, analytics, HTML export, risk scoring
"""

import re
import json
import csv
import argparse
import datetime
import sys
import os
import pickle
from collections import defaultdict

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
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

init(autoreset=True)
LOG_FILE = "phone_osint.log"
CACHE_FILE = "phone_osint_cache.pkl"
HISTORY_FILE = "phone_osint_history.json"
STATS_FILE = "phone_osint_stats.json"

# ========== MEJORA 1: CACHÉ LOCAL ==========
class PhoneCache:
    """Caché para evitar re-analizar números."""
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load()

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "rb") as f:
                    return pickle.load(f)
            except:
                return {}
        return {}

    def get(self, number):
        return self.cache.get(number)

    def set(self, number, data):
        self.cache[number] = data
        self._save()

    def _save(self):
        with open(self.cache_file, "wb") as f:
            pickle.dump(self.cache, f)

    def clear(self):
        self.cache = {}
        self._save()

cache = PhoneCache()

# ========== MEJORA 2: ESTADÍSTICAS Y HISTORIAL ==========
class Analytics:
    """Seguimiento de búsquedas y estadísticas."""
    def __init__(self, history_file=HISTORY_FILE, stats_file=STATS_FILE):
        self.history_file = history_file
        self.stats_file = stats_file
        self.history = self._load_history()
        self.stats = self._load_stats()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return self._default_stats()
        return self._default_stats()

    def _default_stats(self):
        return {
            "total_queries": 0,
            "valid_numbers": 0,
            "invalid_numbers": 0,
            "countries": {},
            "carriers": {},
            "line_types": {}
        }

    def add_query(self, number, result):
        """Añade consulta al historial."""
        self.history.append({
            "number": number,
            "timestamp": self._timestamp(),
            "valid": result.get("valid", False)
        })
        
        self.stats["total_queries"] += 1
        if result.get("valid"):
            self.stats["valid_numbers"] += 1
            country = result.get("country", {}).get("value", "UNKNOWN")
            self.stats["countries"][country] = self.stats["countries"].get(country, 0) + 1
            carrier_val = result.get("carrier", {}).get("value", "UNKNOWN")
            self.stats["carriers"][carrier_val] = self.stats["carriers"].get(carrier_val, 0) + 1
            line = result.get("line_type", {}).get("value", "UNKNOWN")
            self.stats["line_types"][line] = self.stats["line_types"].get(line, 0) + 1
        else:
            self.stats["invalid_numbers"] += 1
        
        self._save()

    def _timestamp(self):
        try:
            return datetime.datetime.now(datetime.UTC).isoformat()
        except AttributeError:
            return datetime.datetime.utcnow().isoformat()

    def _save(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def show_stats(self):
        """Muestra estadísticas en pantalla."""
        print(Fore.CYAN + Style.BRIGHT + "\n═══════ ESTADÍSTICAS GLOBALES ═══════")
        print(f"Total de consultas: {Fore.GREEN}{self.stats['total_queries']}")
        print(f"Números válidos: {Fore.GREEN}{self.stats['valid_numbers']}")
        print(f"Números inválidos: {Fore.RED}{self.stats['invalid_numbers']}")
        
        if self.stats['countries']:
            print(f"\n{Fore.CYAN}Top Países:")
            top = sorted(self.stats['countries'].items(), key=lambda x: x[1], reverse=True)[:5]
            for country, count in top:
                print(f"  • {country}: {Fore.GREEN}{count}")
        
        if self.stats['carriers']:
            print(f"\n{Fore.CYAN}Top Operadores:")
            top = sorted(self.stats['carriers'].items(), key=lambda x: x[1], reverse=True)[:5]
            for car, count in top:
                print(f"  • {car}: {Fore.GREEN}{count}")

analytics = Analytics()

# ========== FUNCIONES AUXILIARES ==========
def banner():
    print(Fore.CYAN + Style.BRIGHT + r"""
 ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗
 ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝
 ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  
 ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  
 ██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗
 ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
""")
    print(Fore.WHITE + "        Phone OSINT Tool Pro — Ethical & Professional\n")

def section(title: str):
    print(Fore.CYAN + Style.BRIGHT + f"\n── {title} ──────────────────────────────")

def format_value(value, confidence):
    color = {"HIGH": Fore.GREEN, "MEDIUM": Fore.YELLOW, "LOW": Fore.MAGENTA, "NONE": Fore.RED}.get(confidence, Fore.WHITE)
    return color + f"{value} [{confidence}]"

def log_event(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        try:
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        except AttributeError:
            timestamp = datetime.datetime.utcnow().isoformat()
        f.write(f"[{timestamp}] {msg}\n")

# ========== NORMALIZACIÓN E ANÁLISIS ==========
def normalize_input(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if not cleaned.startswith("+"):
        raise ValueError("Formato inválido: se requiere código de país (E.164). Ejemplo: +5491155667788")
    return cleaned

# ========== MEJORA 3: VALIDACIÓN DE RIESGO ==========
def _calculate_risk_score(result: dict) -> dict:
    """Calcula un score de riesgo del número."""
    score = 0
    reasons = []
    
    if not result.get("valid"):
        return {"score": 100, "level": "CRÍTICO", "reasons": ["Número inválido"]}
    
    carrier_val = result.get("carrier", {}).get("value", "")
    if "NOT DETERMINABLE" in carrier_val:
        score += 10
        reasons.append("Operador no determinable")
    
    region = result.get("region", {}).get("value", "")
    if region == "UNKNOWN":
        score += 15
        reasons.append("Región desconocida")
    
    level = "BAJO" if score < 30 else "MEDIO" if score < 60 else "ALTO"
    return {"score": score, "level": level, "reasons": reasons if reasons else ["Sin alertas"]}

def analyze_number(raw_number: str) -> dict:
    """Analiza un número telefónico."""
    result = {"input_original": raw_number}

    try:
        normalized = normalize_input(raw_number)
        result["input_normalized"] = normalized
    except ValueError as e:
        result["error"] = str(e)
        return result

    # Verificar caché (MEJORA 1)
    cached = cache.get(normalized)
    if cached:
        return {**cached, "_from_cache": True}

    try:
        num = phonenumbers.parse(normalized, None)
    except phonenumbers.NumberParseException:
        result["error"] = "Formato de número inválido"
        return result

    result["valid"] = phonenumbers.is_valid_number(num)
    if not result["valid"]:
        return result

    # Análisis
    country = geocoder.description_for_number(num, "es") or "UNKNOWN"
    result["country"] = {"value": country, "confidence": "HIGH" if country != "UNKNOWN" else "NONE"}

    region = geocoder.description_for_number(num, "en") or "UNKNOWN"
    result["region"] = {"value": region, "confidence": "MEDIUM" if region != "UNKNOWN" else "NONE"}

    car = carrier.name_for_number(num, "es")
    result["carrier"] = {"value": car or "NOT DETERMINABLE", "confidence": "MEDIUM" if car else "NONE"}

    result["line_type"] = {"value": PhoneNumberType.to_string(number_type(num)), "confidence": "MEDIUM"}

    tzs = timezone.time_zones_for_number(num)
    result["timezones"] = {"value": ", ".join(tzs) if tzs else "NOT DETERMINABLE", "confidence": "HIGH" if tzs and len(tzs) == 1 else "MEDIUM"}

    result["formats"] = {
        "e164": phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164),
        "international": phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "national": phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.NATIONAL),
    }

    result["risk_score"] = _calculate_risk_score(result)
    cache.set(normalized, result)
    return result

def print_output(data: dict):
    """Imprime resultados en consola."""
    banner()

    if "error" in data:
        section("ERROR")
        print(Fore.RED + "❌ " + data["error"])
        return

    if not data.get("valid"):
        section("RESULTADO")
        print(f"📥 Original     : {data['input_original']}")
        print(f"🧼 Normalizado  : {Fore.RED}{data['input_normalized']}")
        print(Fore.RED + "❌ Número inválido según estándares E.164")
        return

    from_cache = " (desde caché)" if data.get("_from_cache") else ""
    section("INPUT")
    print(f"📥 Original     : {data['input_original']}")
    print(f"🧼 Normalizado  : {Fore.GREEN}{data['input_normalized']}{from_cache}")
    print(f"✔ Válido       : {Fore.GREEN}{data['valid']}")

    section("ANÁLISIS")
    print("🌍 País        :", format_value(**data["country"]))
    print("📍 Región      :", format_value(**data["region"]))
    print("📡 Operador    :", format_value(**data["carrier"]))
    print("📶 Tipo línea  :", format_value(**data["line_type"]))
    print("🕒 Zona horaria:", format_value(**data["timezones"]))

    risk = data.get("risk_score", {})
    risk_color = {"BAJO": Fore.GREEN, "MEDIO": Fore.YELLOW, "ALTO": Fore.RED, "CRÍTICO": Fore.RED + Style.BRIGHT}.get(risk.get("level", ""), Fore.WHITE)
    print(f"\n⚠️  Risk Score  : {risk_color}{risk.get('score', 0)}/100 [{risk.get('level', 'N/A')}]")
    for reason in risk.get("reasons", []):
        print(f"   • {reason}")

    section("FORMATOS")
    print("📞 E.164        :", data["formats"]["e164"])
    print("🌐 Internacional:", data["formats"]["international"])
    print("🏠 Nacional     :", data["formats"]["national"])

    section("NOTAS")
    print(Fore.YELLOW + "⚠️ Información basada en estándares públicos.")
    print(Fore.YELLOW + "⚠️ No garantiza precisión ni ubicación exacta.")

    print(Fore.CYAN + "\n──────────────────────────────────────\n")

# ========== MEJORA 5: PROCESAMIENTO POR LOTES ==========
def batch_analyze(numbers: list) -> list:
    """Analiza múltiples números."""
    results = []
    for num in numbers:
        result = analyze_number(num)
        results.append(result)
        analytics.add_query(num, result)
        log_event(f"Query: {num} | Valid: {result.get('valid')}")
    return results

# ========== MEJORA 6: CARGAR DESDE CSV ==========
def load_from_csv(filepath: str) -> list:
    """Carga números desde archivo CSV."""
    numbers = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    numbers.append(row[0].strip())
        return numbers
    except Exception as e:
        print(Fore.RED + f"❌ Error al leer CSV: {e}")
        return []

# ========== MEJORA 7: EXPORTAR CSV ==========
def export_batch_csv(results: list, filename="phone_osint_batch.csv"):
    """Exporta resultados de lote a CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["original", "normalized", "valid", "country", "region", "carrier", "risk_level"])
        writer.writeheader()
        for result in results:
            if "error" not in result:
                writer.writerow({
                    "original": result.get("input_original", ""),
                    "normalized": result.get("input_normalized", ""),
                    "valid": result.get("valid", False),
                    "country": result.get("country", {}).get("value", ""),
                    "region": result.get("region", {}).get("value", ""),
                    "carrier": result.get("carrier", {}).get("value", ""),
                    "risk_level": result.get("risk_score", {}).get("level", "")
                })
    print(Fore.GREEN + f"✔ Exportado a {filename}")

# ========== MEJORA 4: EXPORTAR HTML ==========
def export_html(data: dict, filename="phone_osint_output.html"):
    """Exporta resultado a HTML."""
    if "error" in data:
        html = f"""<html><body><h1>Error</h1><p>{data['error']}</p></body></html>"""
    else:
        risk = data.get("risk_score", {})
        html = f"""<html>
<head><meta charset="utf-8"><style>
body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
.container {{ background: white; padding: 20px; border-radius: 5px; }}
.section {{ background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
.value {{ color: #007bff; font-weight: bold; }}
.risk {{ padding: 10px; border-radius: 3px; }}
.risk.bajo {{ background: #d4edda; color: #155724; }}
.risk.medio {{ background: #fff3cd; color: #856404; }}
.risk.alto {{ background: #f8d7da; color: #721c24; }}
</style></head>
<body><div class="container">
<h1>📱 Phone OSINT Report</h1>
<div class="section">
  <h3>Input</h3>
  <p><strong>Original:</strong> <span class="value">{data['input_original']}</span></p>
  <p><strong>Normalized:</strong> <span class="value">{data['input_normalized']}</span></p>
  <p><strong>Valid:</strong> <span class="value">{data['valid']}</span></p>
</div>
<div class="section">
  <h3>Analysis</h3>
  <p><strong>Country:</strong> {data['country']['value']} ({data['country']['confidence']})</p>
  <p><strong>Carrier:</strong> {data['carrier']['value']} ({data['carrier']['confidence']})</p>
  <p><strong>Line Type:</strong> {data['line_type']['value']}</p>
  <p><strong>Timezones:</strong> {data['timezones']['value']}</p>
</div>
<div class="section">
  <h3>Risk Assessment</h3>
  <div class="risk {risk.get('level', '').lower()}">
    <strong>Risk Score:</strong> {risk.get('score', 0)}/100 - {risk.get('level', 'N/A')}<br>
    {"".join(f"<li>{r}</li>" for r in risk.get('reasons', []))}
  </div>
</div>
<div class="section">
  <h3>Formats</h3>
  <p><strong>E.164:</strong> <span class="value">{data['formats']['e164']}</span></p>
  <p><strong>International:</strong> <span class="value">{data['formats']['international']}</span></p>
  <p><strong>National:</strong> <span class="value">{data['formats']['national']}</span></p>
</div>
</div></body></html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(Fore.GREEN + f"✔ Exportado a {filename}")

# ========== MEJORA 8: FILTRAR RESULTADOS ==========
def filter_results(results: list, country: str = None, carrier_name: str = None) -> list:
    """Filtra resultados por país u operador."""
    filtered = results
    if country:
        filtered = [r for r in filtered if country.lower() in r.get("country", {}).get("value", "").lower()]
    if carrier_name:
        filtered = [r for r in filtered if carrier_name.lower() in r.get("carrier", {}).get("value", "").lower()]
    return filtered

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Phone OSINT Tool Pro")

    parser.add_argument("number", nargs="?", help="Número en formato E.164 (ej: +5491155667788)")
    parser.add_argument("--json", action="store_true", help="Exportar a JSON")
    parser.add_argument("--csv", action="store_true", help="Exportar a CSV")
    parser.add_argument("--html", action="store_true", help="Exportar a HTML")
    parser.add_argument("--batch", type=str, help="Múltiples números separados por comas")
    parser.add_argument("--csv-input", type=str, help="Cargar desde archivo CSV")
    parser.add_argument("--csv-output", type=str, help="Guardar lote en CSV")
    parser.add_argument("--country", type=str, help="Filtrar por país")
    parser.add_argument("--carrier", type=str, help="Filtrar por operador")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--history", action="store_true", help="Mostrar historial")
    parser.add_argument("--clear-cache", action="store_true", help="Limpiar caché")

    args = parser.parse_args()

    if args.stats:
        analytics.show_stats()
        return

    if args.history:
        if analytics.history:
            print(Fore.CYAN + "\n═══════ HISTORIAL (últimas 20) ═══════")
            for entry in analytics.history[-20:]:
                print(f"  {entry['timestamp']}: {entry['number']} (valid: {entry['valid']})")
        else:
            print(Fore.YELLOW + "El historial está vacío.")
        return

    if args.clear_cache:
        cache.clear()
        print(Fore.GREEN + "✔ Caché limpiado")
        return

    numbers = []
    if args.batch:
        numbers = [n.strip() for n in args.batch.split(",")]
    elif args.csv_input:
        numbers = load_from_csv(args.csv_input)
    elif args.number:
        numbers = [args.number]
    else:
        parser.print_help()
        return

    if len(numbers) == 1:
        # Análisis simple
        data = analyze_number(numbers[0])
        print_output(data)
        analytics.add_query(numbers[0], data)
        log_event(f"Query: {numbers[0]} | Valid: {data.get('valid')}")

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

        if args.html:
            export_html(data)
    else:
        # Análisis por lotes
        banner()
        print(Fore.CYAN + f"\n📊 Analizando {len(numbers)} números...\n")
        results = batch_analyze(numbers)

        filtered_results = results
        if args.country:
            filtered_results = filter_results(filtered_results, country=args.country)
        if args.carrier:
            filtered_results = filter_results(filtered_results, carrier_name=args.carrier)

        valid_count = sum(1 for r in filtered_results if r.get("valid"))
        invalid_count = sum(1 for r in filtered_results if not r.get("valid") and "error" not in r)
        error_count = sum(1 for r in filtered_results if "error" in r)

        print(Fore.GREEN + f"✔ Válidos: {valid_count}")
        print(Fore.YELLOW + f"⚠ Inválidos: {invalid_count}")
        print(Fore.RED + f"❌ Errores: {error_count}")

        if args.csv_output:
            export_batch_csv(filtered_results, args.csv_output)
        elif args.csv:
            export_batch_csv(filtered_results)

if __name__ == "__main__":
    main()
