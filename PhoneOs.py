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
from pathlib import Path

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

# Importar módulos avanzados (opcional)
try:
    import folium
    from geopy.geocoders import Nominatim
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from datetime import datetime as dt
    from flask import Flask, request, jsonify
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

from colorama import Fore, Style, init

init(autoreset=True)
LOG_FILE = "phone_osint.log"
CACHE_FILE = "phone_osint_cache.pkl"
HISTORY_FILE = "phone_osint_history.json"
STATS_FILE = "phone_osint_stats.json"
OUTPUTS_DIR = "outputs"  # Directorio base para outputs organizados

# ========== MEJORA 11: ORGANIZACIÓN DE OUTPUTS ==========
def get_number_output_dir(number: str) -> str:
    """Crea y retorna la carpeta para output de un número."""
    # Sanitizar número para nombre de carpeta
    safe_number = number.replace("+", "").replace(" ", "_")
    output_path = os.path.join(OUTPUTS_DIR, safe_number)
    Path(output_path).mkdir(parents=True, exist_ok=True)
    return output_path

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
def export_batch_csv(results: list, filename: str = None):
    """Exporta resultados de lote a CSV en carpeta organizada."""
    if filename is None:
        # Crear carpeta para lotes si no existe
        batch_dir = os.path.join(OUTPUTS_DIR, "batch_reports")
        Path(batch_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(batch_dir, f"batch_{timestamp}.csv")
    else:
        # Si no tiene directorio, ponerlo en batch_reports
        if os.path.dirname(filename) == "":
            batch_dir = os.path.join(OUTPUTS_DIR, "batch_reports")
            Path(batch_dir).mkdir(parents=True, exist_ok=True)
            filename = os.path.join(batch_dir, filename)
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
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
def export_html(data: dict, filename: str = None):
    """Exporta resultado a HTML en carpeta organizada."""
    # Si no se especifica filename, crear uno en carpeta del número
    if filename is None and "input_normalized" in data:
        output_dir = get_number_output_dir(data["input_normalized"])
        filename = os.path.join(output_dir, "reporte.html")
    elif filename is None:
        filename = "phone_osint_output.html"
    
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
  <p><strong>Country:</strong> {data.get('country', {}).get('value', 'N/A')} ({data.get('country', {}).get('confidence', 'N/A')})</p>
  <p><strong>Carrier:</strong> {data.get('carrier', {}).get('value', 'N/A')} ({data.get('carrier', {}).get('confidence', 'N/A')})</p>
  <p><strong>Line Type:</strong> {data.get('line_type', {}).get('value', 'N/A')}</p>
  <p><strong>Timezones:</strong> {data.get('timezones', {}).get('value', 'N/A')}</p>
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
  <p><strong>E.164:</strong> <span class="value">{data.get('formats', {}).get('e164', 'N/A')}</span></p>
  <p><strong>International:</strong> <span class="value">{data.get('formats', {}).get('international', 'N/A')}</span></p>
  <p><strong>National:</strong> <span class="value">{data.get('formats', {}).get('national', 'N/A')}</span></p>
</div>
</div></body></html>"""
    
    # Crear carpeta si es necesario
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
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

# ========== MEJORA 12: GEOLOCALIZACIÓN CON MAPAS ==========
def generate_geolocation_map(country: str, region: str, output_path: str) -> bool:
    """Genera mapa interactivo con folium."""
    if not ADVANCED_FEATURES:
        print(Fore.YELLOW + "⚠️ Características avanzadas no disponibles. Instala: folium geopy")
        return False
    
    try:
        geolocator = Nominatim(user_agent="phoneoispro")
        location_str = f"{region}, {country}" if region else country
        location = geolocator.geocode(location_str, timeout=10)
        
        if not location:
            print(Fore.YELLOW + "⚠️ No se pudo geolocalizar la ubicación")
            return False
        
        # Crear mapa
        m = folium.Map(
            location=[location.latitude, location.longitude],
            zoom_start=8,
            tiles="OpenStreetMap"
        )
        
        # Añadir marcador
        folium.Marker(
            location=[location.latitude, location.longitude],
            popup=f"{region}, {country}",
            tooltip=location.address,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        # Círculo de cobertura aproximada (50km)
        folium.Circle(
            location=[location.latitude, location.longitude],
            radius=50000,
            popup="Área aproximada (50km)",
            color="blue",
            fill=True,
            fillOpacity=0.1
        ).add_to(m)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        m.save(output_path)
        return True
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Error al generar mapa: {e}")
        return False

# ========== MEJORA 13: BÚSQUEDA INVERSA DE EMAILS ==========
def search_emails_osint(phone: str, country: str = None) -> dict:
    """Búsqueda OSINT de emails asociados (simulada)."""
    results = {
        "phone": phone,
        "search_type": "OSINT Local Simulation",
        "note": "⚠️ Esta es una búsqueda educativa simulada. En producción requiere APIs como Hunter.io",
        "country": country,
        "possible_domains": []
    }
    
    # Dominios comunes por país (referencia educativa)
    country_domains = {
        "Argentina": ["ar.com", "com.ar", "mail.ar"],
        "México": ["com.mx", "mx.com"],
        "Spain": ["es.com", "com.es", ".es"],
        "United States": ["gmail.com", "outlook.com", ".us"],
    }
    
    domains = country_domains.get(country, ["gmail.com", "outlook.com", "mail.com"])
    results["possible_domains"] = domains
    results["method"] = "OSINT - Análisis de patrones públicos"
    
    return results

# ========== MEJORA 14: GENERACIÓN DE REPORTES PDF ==========
def generate_pdf_report(data: dict, output_path: str) -> bool:
    """Genera reporte PDF profesional."""
    if not ADVANCED_FEATURES:
        print(Fore.YELLOW + "⚠️ PDF no disponible. Instala: reportlab")
        return False
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#007bff'),
            spaceAfter=30,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#007bff'),
            spaceBefore=12,
            spaceAfter=6
        )
        
        # Título
        story.append(Paragraph("📱 PHONE OSINT REPORT", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Información básica
        story.append(Paragraph("Información del Número", heading_style))
        
        basic_data = [
            ["Campo", "Valor"],
            ["Número Original", data.get("input_original", "N/A")],
            ["Número Normalizado", data.get("input_normalized", "N/A")],
            ["¿Válido?", "✓ Sí" if data.get("valid") else "✗ No"],
        ]
        
        table = Table(basic_data, colWidths=[2*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Análisis
        if data.get("valid"):
            story.append(Paragraph("Análisis Detallado", heading_style))
            
            analysis_data = [
                ["Atributo", "Valor", "Confianza"],
                ["País", data.get("country", {}).get("value", "N/A"), data.get("country", {}).get("confidence", "N/A")],
                ["Región", data.get("region", {}).get("value", "N/A"), data.get("region", {}).get("confidence", "N/A")],
                ["Operador", data.get("carrier", {}).get("value", "N/A"), data.get("carrier", {}).get("confidence", "N/A")],
                ["Tipo de Línea", data.get("line_type", {}).get("value", "N/A"), "MEDIUM"],
                ["Zona Horaria", data.get("timezones", {}).get("value", "N/A"), data.get("timezones", {}).get("confidence", "N/A")],
            ]
            
            analysis_table = Table(analysis_data, colWidths=[1.8*inch, 2*inch, 1.7*inch])
            analysis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            
            story.append(analysis_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Risk Score
            risk = data.get("risk_score", {})
            story.append(Paragraph("Evaluación de Riesgo", heading_style))
            
            risk_data = [
                ["Risk Score", f"{risk.get('score', 0)}/100"],
                ["Nivel de Riesgo", risk.get('level', 'N/A')],
                ["Razones", ", ".join(risk.get("reasons", []))[:100]],
            ]
            
            risk_table = Table(risk_data, colWidths=[2*inch, 3.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            
            story.append(risk_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Formatos
            story.append(Paragraph("Formatos de Número", heading_style))
            
            formats_data = [
                ["Formato", "Valor"],
                ["E.164", data.get("formats", {}).get("e164", "N/A")],
                ["Internacional", data.get("formats", {}).get("international", "N/A")],
                ["Nacional", data.get("formats", {}).get("national", "N/A")],
            ]
            
            formats_table = Table(formats_data, colWidths=[2*inch, 3.5*inch])
            formats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            
            story.append(formats_table)
        
        # Pie de página
        story.append(Spacer(1, 0.5*inch))
        try:
            timestamp = dt.now().strftime('%Y-%m-%d %H:%M:%S')
            footer_text = f"<i>Reporte generado: {timestamp}</i>"
            story.append(Paragraph(footer_text, styles['Normal']))
        except:
            pass
        
        story.append(Paragraph("<i>⚠️ Información basada en estándares públicos. No garantiza precisión.</i>", styles['Normal']))
        
        # Generar PDF
        doc.build(story)
        return True
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Error al generar PDF: {e}")
        return False

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
    
    # ========== MEJORAS AVANZADAS ==========
    parser.add_argument("--map", action="store_true", help="Generar mapa de geolocalización")
    parser.add_argument("--email", action="store_true", help="Buscar emails asociados (OSINT)")
    parser.add_argument("--pdf", action="store_true", help="Generar reporte PDF profesional")
    parser.add_argument("--web-server", action="store_true", help="Iniciar API REST + Dashboard")

    args = parser.parse_args()
    
    # ========== MEJORA 15: SERVIDOR WEB + API REST (PRIMERO) ==========
    if args.web_server:
        print(Fore.CYAN + "\n🚀 Iniciando API REST + Dashboard...")
        print(Fore.CYAN + "📱 Abre: http://localhost:8000")
        print(Fore.YELLOW + "⚠️ Presiona Ctrl+C para detener\n")
        
        # Crear una aplicación Flask simple
        app = Flask(__name__)
        
        # Configurar CORS
        try:
            from flask_cors import CORS
            CORS(app)
        except:
            pass
        
        @app.route('/')
        def dashboard():
            """Dashboard HTML"""
            html = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Phone OSINT Pro - Dashboard</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        padding: 40px;
                    }
                    h1 {
                        color: #667eea;
                        margin-bottom: 10px;
                        text-align: center;
                    }
                    .subtitle {
                        text-align: center;
                        color: #666;
                        margin-bottom: 30px;
                    }
                    .input-group {
                        margin-bottom: 20px;
                    }
                    label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: bold;
                        color: #333;
                    }
                    input[type="text"] {
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #ddd;
                        border-radius: 5px;
                        font-size: 16px;
                        transition: border-color 0.3s;
                    }
                    input[type="text"]:focus {
                        outline: none;
                        border-color: #667eea;
                    }
                    .options {
                        display: flex;
                        gap: 10px;
                        margin-bottom: 20px;
                        flex-wrap: wrap;
                    }
                    .checkbox {
                        display: flex;
                        align-items: center;
                        gap: 5px;
                    }
                    button {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        cursor: pointer;
                        transition: transform 0.2s;
                    }
                    button:hover {
                        transform: translateY(-2px);
                    }
                    button:active {
                        transform: translateY(0);
                    }
                    .result {
                        background: #f5f5f5;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        border-radius: 5px;
                        margin-top: 30px;
                        max-height: 500px;
                        overflow-y: auto;
                    }
                    .result pre {
                        font-size: 13px;
                        color: #333;
                        white-space: pre-wrap;
                        word-break: break-word;
                    }
                    .error {
                        background: #fee;
                        border-left-color: #f00;
                        color: #c33;
                    }
                    .loading {
                        text-align: center;
                        color: #667eea;
                    }
                    .spinner {
                        border: 4px solid #ddd;
                        border-top: 4px solid #667eea;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    .info {
                        background: #e8f4f8;
                        border-left-color: #667eea;
                        padding: 15px;
                        border-radius: 5px;
                        margin-top: 20px;
                        font-size: 14px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📱 Phone OSINT Pro</h1>
                    <div class="subtitle">Análisis Avanzado de Números de Teléfono</div>
                    
                    <div class="input-group">
                        <label for="phone">Número de Teléfono (E.164):</label>
                        <input type="text" id="phone" placeholder="+5491155667788" value="">
                    </div>
                    
                    <div class="options">
                        <div class="checkbox">
                            <input type="checkbox" id="mapCheck" checked>
                            <label for="mapCheck">🗺️ Mapa</label>
                        </div>
                        <div class="checkbox">
                            <input type="checkbox" id="emailCheck" checked>
                            <label for="emailCheck">📧 Emails OSINT</label>
                        </div>
                        <div class="checkbox">
                            <input type="checkbox" id="pdfCheck">
                            <label for="pdfCheck">📄 PDF</label>
                        </div>
                    </div>
                    
                    <button onclick="analyzePhone()">🔍 Analizar</button>
                    
                    <div id="result"></div>
                    
                    <div class="info">
                        💡 <strong>Consejo:</strong> Ingresa números en formato internacional (+país-área-número). 
                        Ej: +1-202-555-0173 (USA), +34-91-555-1234 (España)
                    </div>
                </div>
                
                <script>
                    function analyzePhone() {
                        const phone = document.getElementById('phone').value.trim();
                        if (!phone) {
                            showResult('Por favor ingresa un número', true);
                            return;
                        }
                        
                        const resultDiv = document.getElementById('result');
                        resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analizando...</p></div>';
                        
                        fetch('/api/analyze', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                phone: phone,
                                map: document.getElementById('mapCheck').checked,
                                email: document.getElementById('emailCheck').checked,
                                pdf: document.getElementById('pdfCheck').checked
                            })
                        })
                        .then(r => r.json())
                        .then(data => {
                            if (data.error) {
                                showResult(data.error, true);
                            } else {
                                showResult(JSON.stringify(data, null, 2), false);
                            }
                        })
                        .catch(err => showResult('Error: ' + err, true));
                    }
                    
                    function showResult(text, isError) {
                        const resultDiv = document.getElementById('result');
                        resultDiv.className = 'result' + (isError ? ' error' : '');
                        resultDiv.innerHTML = '<pre>' + text + '</pre>';
                    }
                    
                    document.getElementById('phone').addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') analyzePhone();
                    });
                </script>
            </body>
            </html>
            """
            return html
        
        @app.route('/api/analyze', methods=['POST'])
        def api_analyze():
            """API REST para análisis"""
            data = request.json
            phone = data.get('phone', '')
            
            if not phone:
                return {'error': 'Teléfono no proporcionado'}, 400
            
            try:
                result = analyze_number(phone)
                analytics.add_query(phone, result)
                
                # Agregar datos adicionales
                if data.get('email') and result.get('valid'):
                    result['emails_osint'] = search_emails_osint(phone, result.get('country', {}).get('value', ''))
                
                return result
            except Exception as e:
                return {'error': str(e)}, 400
        
        @app.route('/api/stats', methods=['GET'])
        def api_stats():
            """API para estadísticas"""
            return {
                'total_queries': len(analytics.history),
                'countries': analytics.stats.get('countries', {}),
                'carriers': analytics.stats.get('carriers', {})
            }
        
        try:
            app.run(host='localhost', port=8000, debug=False)
        except KeyboardInterrupt:
            print(Fore.CYAN + "\n✔ Servidor detenido")
        except Exception as e:
            print(Fore.RED + f"❌ Error al iniciar servidor: {e}")
        return

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

        if not "error" in data and data.get("valid"):
            # Crear carpeta para este número
            output_dir = get_number_output_dir(data.get("input_normalized", numbers[0]))
            
            if args.json:
                json_path = os.path.join(output_dir, "resultado.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(Fore.GREEN + f"✔ Exportado a {json_path}")

            if args.csv:
                csv_path = os.path.join(output_dir, "resultado.csv")
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for k, v in data.items():
                        writer.writerow([k, v])
                print(Fore.GREEN + f"✔ Exportado a {csv_path}")

            if args.html:
                export_html(data)
            
            # ========== MEJORA 12: MAPA DE GEOLOCALIZACIÓN ==========
            if args.map:
                country = data.get("country", {}).get("value", "")
                region = data.get("region", {}).get("value", "")
                if country:
                    map_path = os.path.join(output_dir, "mapa.html")
                    print(Fore.CYAN + "\n🗺️ Generando mapa de geolocalización...")
                    if generate_geolocation_map(country, region, map_path):
                        print(Fore.GREEN + f"✔ Mapa generado: {map_path}")
                    else:
                        print(Fore.YELLOW + "⚠️ No se pudo generar el mapa")
                else:
                    print(Fore.YELLOW + "⚠️ No se pudo extraer información de país para el mapa")
            
            # ========== MEJORA 13: BÚSQUEDA DE EMAILS ==========
            if args.email:
                country = data.get("country", {}).get("value", "")
                print(Fore.CYAN + "\n📧 Buscando emails asociados (OSINT)...")
                email_results = search_emails_osint(numbers[0], country)
                print(Fore.MAGENTA + f"  Dominios posibles: {', '.join(email_results.get('possible_domains', []))}")
                
                # Guardar emails en JSON
                emails_path = os.path.join(output_dir, "emails_osint.json")
                with open(emails_path, "w", encoding="utf-8") as f:
                    json.dump(email_results, f, indent=4, ensure_ascii=False)
                print(Fore.GREEN + f"✔ Datos de OSINT guardados: {emails_path}")
            
            # ========== MEJORA 14: GENERACIÓN DE PDF ==========
            if args.pdf:
                print(Fore.CYAN + "\n📄 Generando reporte PDF...")
                pdf_path = os.path.join(output_dir, "reporte_profesional.pdf")
                if generate_pdf_report(data, pdf_path):
                    print(Fore.GREEN + f"✔ Reporte PDF generado: {pdf_path}")
                else:
                    print(Fore.YELLOW + "⚠️ No se pudo generar el PDF")
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
    
    # ========== MEJORA 15: SERVIDOR WEB + API REST ==========
    if args.web_server:
        print(Fore.CYAN + "\n🚀 Iniciando API REST + Dashboard...")
        print(Fore.CYAN + "📱 Abre: http://localhost:8000")
        print(Fore.YELLOW + "⚠️ Presiona Ctrl+C para detener\n")
        
        # Crear una aplicación Flask simple
        app = Flask(__name__)
        
        # Configurar CORS
        try:
            from flask_cors import CORS
            CORS(app)
        except:
            pass
        
        @app.route('/')
        def dashboard():
            """Dashboard HTML"""
            html = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Phone OSINT Pro - Dashboard</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        padding: 40px;
                    }
                    h1 {
                        color: #667eea;
                        margin-bottom: 10px;
                        text-align: center;
                    }
                    .subtitle {
                        text-align: center;
                        color: #666;
                        margin-bottom: 30px;
                    }
                    .input-group {
                        margin-bottom: 20px;
                    }
                    label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: bold;
                        color: #333;
                    }
                    input[type="text"] {
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #ddd;
                        border-radius: 5px;
                        font-size: 16px;
                        transition: border-color 0.3s;
                    }
                    input[type="text"]:focus {
                        outline: none;
                        border-color: #667eea;
                    }
                    .options {
                        display: flex;
                        gap: 10px;
                        margin-bottom: 20px;
                        flex-wrap: wrap;
                    }
                    .checkbox {
                        display: flex;
                        align-items: center;
                        gap: 5px;
                    }
                    button {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 12px 30px;
                        font-size: 16px;
                        border-radius: 5px;
                        cursor: pointer;
                        transition: transform 0.2s;
                    }
                    button:hover {
                        transform: translateY(-2px);
                    }
                    button:active {
                        transform: translateY(0);
                    }
                    .result {
                        background: #f5f5f5;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        border-radius: 5px;
                        margin-top: 30px;
                        max-height: 500px;
                        overflow-y: auto;
                    }
                    .result pre {
                        font-size: 13px;
                        color: #333;
                        white-space: pre-wrap;
                        word-break: break-word;
                    }
                    .error {
                        background: #fee;
                        border-left-color: #f00;
                        color: #c33;
                    }
                    .loading {
                        text-align: center;
                        color: #667eea;
                    }
                    .spinner {
                        border: 4px solid #ddd;
                        border-top: 4px solid #667eea;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    .info {
                        background: #e8f4f8;
                        border-left-color: #667eea;
                        padding: 15px;
                        border-radius: 5px;
                        margin-top: 20px;
                        font-size: 14px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📱 Phone OSINT Pro</h1>
                    <div class="subtitle">Análisis Avanzado de Números de Teléfono</div>
                    
                    <div class="input-group">
                        <label for="phone">Número de Teléfono (E.164):</label>
                        <input type="text" id="phone" placeholder="+5491155667788" value="">
                    </div>
                    
                    <div class="options">
                        <div class="checkbox">
                            <input type="checkbox" id="mapCheck" checked>
                            <label for="mapCheck">🗺️ Mapa</label>
                        </div>
                        <div class="checkbox">
                            <input type="checkbox" id="emailCheck" checked>
                            <label for="emailCheck">📧 Emails OSINT</label>
                        </div>
                        <div class="checkbox">
                            <input type="checkbox" id="pdfCheck">
                            <label for="pdfCheck">📄 PDF</label>
                        </div>
                    </div>
                    
                    <button onclick="analyzePhone()">🔍 Analizar</button>
                    
                    <div id="result"></div>
                    
                    <div class="info">
                        💡 <strong>Consejo:</strong> Ingresa números en formato internacional (+país-área-número). 
                        Ej: +1-202-555-0173 (USA), +34-91-555-1234 (España)
                    </div>
                </div>
                
                <script>
                    function analyzePhone() {
                        const phone = document.getElementById('phone').value.trim();
                        if (!phone) {
                            showResult('Por favor ingresa un número', true);
                            return;
                        }
                        
                        const resultDiv = document.getElementById('result');
                        resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analizando...</p></div>';
                        
                        fetch('/api/analyze', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                phone: phone,
                                map: document.getElementById('mapCheck').checked,
                                email: document.getElementById('emailCheck').checked,
                                pdf: document.getElementById('pdfCheck').checked
                            })
                        })
                        .then(r => r.json())
                        .then(data => {
                            if (data.error) {
                                showResult(data.error, true);
                            } else {
                                showResult(JSON.stringify(data, null, 2), false);
                            }
                        })
                        .catch(err => showResult('Error: ' + err, true));
                    }
                    
                    function showResult(text, isError) {
                        const resultDiv = document.getElementById('result');
                        resultDiv.className = 'result' + (isError ? ' error' : '');
                        resultDiv.innerHTML = '<pre>' + text + '</pre>';
                    }
                    
                    document.getElementById('phone').addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') analyzePhone();
                    });
                </script>
            </body>
            </html>
            """
            return html
        
        @app.route('/api/analyze', methods=['POST'])
        def api_analyze():
            """API REST para análisis"""
            data = request.json
            phone = data.get('phone', '')
            
            if not phone:
                return {'error': 'Teléfono no proporcionado'}, 400
            
            try:
                result = analyze_number(phone)
                analytics.add_query(phone, result)
                
                # Agregar datos adicionales
                if data.get('email') and result.get('valid'):
                    result['emails_osint'] = search_emails_osint(phone, result.get('country', {}).get('value', ''))
                
                return result
            except Exception as e:
                return {'error': str(e)}, 400
        
        @app.route('/api/stats', methods=['GET'])
        def api_stats():
            """API para estadísticas"""
            return {
                'total_queries': len(analytics.history),
                'countries': analytics.stats.get('countries', {}),
                'carriers': analytics.stats.get('carriers', {})
            }
        
        try:
            app.run(host='localhost', port=8000, debug=False)
        except KeyboardInterrupt:
            print(Fore.CYAN + "\n✔ Servidor detenido")
        except Exception as e:
            print(Fore.RED + f"❌ Error al iniciar servidor: {e}")

if __name__ == "__main__":
    main()
