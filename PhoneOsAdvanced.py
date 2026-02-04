#!/usr/bin/env python3
"""
Phone OSINT Pro Advanced Features
Geolocation, Email Validation, PDF Reports, REST API + Dashboard
"""

import os
import json
import folium
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request as flask_request
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from geopy.geocoders import Nominatim
from threading import Thread
import webbrowser

# ========== MEJORA 1: GEOLOCALIZACIÓN CON MAPAS ==========
class GeoLocator:
    """Geolocalización usando OpenStreetMap/Nominatim."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="phoneoispro")
    
    def get_coordinates(self, country: str, region: str = None) -> dict:
        """Obtiene coordenadas de una ubicación."""
        try:
            location_str = f"{region}, {country}" if region else country
            location = self.geolocator.geocode(location_str, timeout=10)
            
            if location:
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "address": location.address,
                    "success": True
                }
            return {"success": False, "error": "No se encontró la ubicación"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_map_html(self, country: str, region: str, output_path: str):
        """Genera mapa interactivo con folium."""
        coords = self.get_coordinates(country, region)
        
        if not coords["success"]:
            return False
        
        # Crear mapa centrado en la ubicación
        m = folium.Map(
            location=[coords["latitude"], coords["longitude"]],
            zoom_start=8,
            tiles="OpenStreetMap"
        )
        
        # Añadir marcador
        folium.Marker(
            location=[coords["latitude"], coords["longitude"]],
            popup=f"{region}, {country}",
            tooltip=coords["address"],
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        # Añadir círculo de cobertura aproximada (50km)
        folium.Circle(
            location=[coords["latitude"], coords["longitude"]],
            radius=50000,
            popup="Área aproximada",
            color="blue",
            fill=True,
            fillOpacity=0.1
        ).add_to(m)
        
        # Guardar mapa
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        m.save(output_path)
        return True

geolocator = GeoLocator()

# ========== MEJORA 3: VALIDACIÓN DE EMAIL ==========
class EmailValidator:
    """Validación de emails asociados a números (OSINT)."""
    
    @staticmethod
    def search_emails_osint(phone: str, country: str = None) -> dict:
        """Búsqueda OSINT de emails asociados."""
        results = {
            "phone": phone,
            "emails_found": [],
            "notes": []
        }
        
        # Nota: Esta es una simulación educativa
        # En producción usarías APIs como Hunter.io, RocketReach, etc.
        
        # Patrón común: email@domain basado en código de país
        country_domains = {
            "Argentina": ["ar.com", "com.ar"],
            "México": ["com.mx"],
            "Spain": ["es.com", "com.es"],
            "United States": ["gmail.com", "outlook.com"],
        }
        
        domains = country_domains.get(country, ["gmail.com", "outlook.com"])
        
        # Simulación: generar patrones posibles (para demostración)
        # En producción sería búsqueda real en bases de datos públicas
        phone_digits = phone.replace("+", "").replace("-", "")[-7:]
        
        results["notes"].append("⚠️ Búsqueda simulada. En producción requiere API de Hunter.io o similar.")
        results["notes"].append(f"📱 Dígitos del teléfono: {phone_digits}")
        results["notes"].append(f"🌍 Dominios asociados a {country}: {', '.join(domains)}")
        
        return results

# ========== MEJORA 4: REPORTES PDF PROFESIONALES ==========
class PDFReportGenerator:
    """Generador de reportes PDF profesionales."""
    
    @staticmethod
    def generate_report(data: dict, output_path: str):
        """Genera reporte PDF completo."""
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
            
            risk_level = risk.get("level", "N/A")
            risk_colors = {"BAJO": colors.green, "MEDIO": colors.orange, "ALTO": colors.red, "CRÍTICO": colors.red}
            
            risk_data = [
                ["Risk Score", f"{risk.get('score', 0)}/100"],
                ["Nivel de Riesgo", risk_level],
                ["Razones", ", ".join(risk.get("reasons", []))],
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
        footer_text = f"<i>Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        story.append(Paragraph(footer_text, styles['Normal']))
        story.append(Paragraph("<i>⚠️ Información basada en estándares públicos de telefonía. No garantiza precisión actual.</i>", styles['Normal']))
        
        # Generar PDF
        doc.build(story)
        return True

# ========== MEJORA 5: API REST + DASHBOARD WEB ==========
app = Flask(__name__)

# HTML del Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Phone OSINT Pro - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        header h1 { font-size: 32px; margin-bottom: 10px; }
        header p { opacity: 0.9; }
        .search-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .search-section h2 { margin-bottom: 15px; color: #333; }
        .input-group { display: flex; gap: 10px; margin-bottom: 15px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        button { padding: 12px 30px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        button:hover { background: #0056b3; }
        .checkbox-group { display: flex; gap: 20px; margin-bottom: 15px; flex-wrap: wrap; }
        .checkbox-group label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
        .results { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .result-item { border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 15px; border-radius: 4px; }
        .result-item h3 { color: #007bff; margin-bottom: 10px; }
        .result-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px; }
        .result-field { }
        .result-field strong { color: #333; }
        .result-field span { color: #666; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-top: 10px; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .loading { text-align: center; padding: 40px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px; margin-top: 15px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 4px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📱 Phone OSINT Pro Dashboard</h1>
            <p>Análisis profesional de números telefónicos con OSINT avanzado</p>
        </header>
        
        <div class="search-section">
            <h2>Búsqueda de Números</h2>
            <div class="input-group">
                <input type="text" id="phoneInput" placeholder="Ingresa número en formato E.164 (ej: +5491155667788)" autofocus>
                <button onclick="analyzeNumber()">Analizar</button>
            </div>
            
            <div class="checkbox-group">
                <label><input type="checkbox" id="mapCheck"> 📍 Generar Mapa</label>
                <label><input type="checkbox" id="emailCheck"> 📧 Buscar Emails</label>
                <label><input type="checkbox" id="pdfCheck"> 📄 Generar PDF</label>
            </div>
        </div>
        
        <div class="results" id="results"></div>
    </div>
    
    <script>
        async function analyzeNumber() {
            const phone = document.getElementById('phoneInput').value;
            if (!phone) {
                alert('Por favor ingresa un número');
                return;
            }
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analizando número...</p></div>';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        phone: phone,
                        generate_map: document.getElementById('mapCheck').checked,
                        find_emails: document.getElementById('emailCheck').checked,
                        generate_pdf: document.getElementById('pdfCheck').checked
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    displayResults(data);
                } else {
                    resultsDiv.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">❌ Error de conexión: ${error.message}</div>`;
            }
        }
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            let html = '';
            
            if (data.success) {
                const d = data.data;
                html = `
                    <div class="result-item">
                        <h3>✓ Análisis Completado</h3>
                        <div class="result-grid">
                            <div class="result-field">
                                <strong>Número Original:</strong><br><span>${d.input_original}</span>
                            </div>
                            <div class="result-field">
                                <strong>Número Normalizado:</strong><br><span>${d.input_normalized}</span>
                            </div>
                            <div class="result-field">
                                <strong>¿Válido?:</strong><br><span>${d.valid ? '✓ Sí' : '✗ No'}</span>
                            </div>
                            <div class="result-field">
                                <strong>País:</strong><br><span>${d.country?.value || 'N/A'}</span>
                            </div>
                            <div class="result-field">
                                <strong>Región:</strong><br><span>${d.region?.value || 'N/A'}</span>
                            </div>
                            <div class="result-field">
                                <strong>Operador:</strong><br><span>${d.carrier?.value || 'N/A'}</span>
                            </div>
                            <div class="result-field">
                                <strong>Tipo de Línea:</strong><br><span>${d.line_type?.value || 'N/A'}</span>
                            </div>
                            <div class="result-field">
                                <strong>Risk Score:</strong><br><span>${d.risk_score?.score || 0}/100</span>
                            </div>
                        </div>
                        <div style="margin-top: 15px;">
                            <strong>Risk Level:</strong>
                            <span class="badge ${d.risk_score?.level === 'BAJO' ? 'badge-success' : d.risk_score?.level === 'MEDIO' ? 'badge-warning' : 'badge-danger'}">
                                ${d.risk_score?.level || 'N/A'}
                            </span>
                        </div>
                    </div>
                `;
                
                if (data.map_generated) {
                    html += '<div class="success">✓ Mapa generado: <a href="' + data.map_path + '" target="_blank">Ver Mapa</a></div>';
                }
                if (data.pdf_generated) {
                    html += '<div class="success">✓ PDF generado: <a href="' + data.pdf_path + '" target="_blank">Descargar PDF</a></div>';
                }
            } else {
                html = `<div class="error">❌ ${data.error}</div>`;
            }
            
            resultsDiv.innerHTML = html;
        }
        
        // Enter para buscar
        document.getElementById('phoneInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeNumber();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API para análisis de números."""
    from PhoneOs import analyze_number, get_number_output_dir
    
    try:
        req_data = flask_request.get_json()
        phone = req_data.get('phone')
        generate_map = req_data.get('generate_map', False)
        find_emails = req_data.get('find_emails', False)
        generate_pdf = req_data.get('generate_pdf', False)
        
        # Análisis básico
        result = analyze_number(phone)
        
        response = {
            "success": True,
            "data": result,
            "map_generated": False,
            "pdf_generated": False,
            "map_path": None,
            "pdf_path": None
        }
        
        # Generar mapa si se solicita
        if generate_map and result.get("valid"):
            output_dir = get_number_output_dir(result["input_normalized"])
            map_path = os.path.join(output_dir, "mapa.html")
            if geolocator.generate_map_html(
                result["country"]["value"],
                result["region"]["value"],
                map_path
            ):
                response["map_generated"] = True
                response["map_path"] = map_path
        
        # Buscar emails si se solicita
        if find_emails and result.get("valid"):
            emails = EmailValidator.search_emails_osint(
                phone,
                result["country"]["value"]
            )
            result["emails_osint"] = emails
        
        # Generar PDF si se solicita
        if generate_pdf and result.get("valid"):
            output_dir = get_number_output_dir(result["input_normalized"])
            pdf_path = os.path.join(output_dir, "reporte_profesional.pdf")
            if PDFReportGenerator.generate_report(result, pdf_path):
                response["pdf_generated"] = True
                response["pdf_path"] = pdf_path
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API para obtener estadísticas."""
    from PhoneOs import analytics
    return jsonify(analytics.stats)

def start_web_server(debug=False, port=8000):
    """Inicia el servidor web."""
    print(f"\n🚀 Servidor web iniciado en: http://localhost:{port}")
    print(f"📊 Dashboard disponible en: http://localhost:{port}")
    print(f"📡 API REST disponible en: http://localhost:{port}/api")
    
    # Abrir navegador automáticamente
    import time
    Thread(target=lambda: (time.sleep(1.5), webbrowser.open(f'http://localhost:{port}'))).start()
    
    app.run(debug=debug, port=port, use_reloader=False)

if __name__ == "__main__":
    start_web_server(port=8000)
