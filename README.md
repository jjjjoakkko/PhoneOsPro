# 📱 Phone OSINT Pro

Herramienta OSINT profesional para análisis de números telefónicos usando estándares públicos.

> ⚠️ **Uso ético:** Solo con fines educativos. Sin acceso a datos privados ni garantía de precisión actual.

## ✨ Características

- ✅ Valida y normaliza números (E.164)
- 🌍 País, región, operador y tipo de línea
- 🕒 Zonas horarias asociadas
- ⚠️ **Risk Score** inteligente de números sospechosos
- 💾 **Caché local** para análisis rápido de números repetidos
- 📊 **Procesamiento por lotes** (batch) de múltiples números
- 📈 **Estadísticas globales** y **historial** de búsquedas
- 📥 **Importar desde CSV** y **exportar a CSV/JSON/HTML**
- 🔍 **Filtros** por país y operador
- 🎨 Salida coloreada en consola y reportes HTML

### 🚀 Mejoras Avanzadas (v2.0+)

- 🗺️ **Geolocalización Interactiva** - Mapas con folium/Nominatim
- 📧 **OSINT de Emails** - Búsqueda de dominios asociados
- 📄 **Reportes PDF Profesionales** - Documentos formateados con reportlab
- 🌐 **API REST + Dashboard Web** - Interfaz gráfica con Flask en `http://localhost:8000`

## 📋 Requisitos

- Python 3.6+
- Dependencias: `phonenumbers`, `colorama`, `tabulate`


## 🚀 Instalación

```bash
# Clonar repositorio
git clone https://github.com/jjjjoakkko/PhoneOsPro.git
cd PhoneOsPro

# Crear entorno virtual
python3 -m venv virtual

# Activar entorno
# Windows (CMD):
.\virtual\Scripts\activate
# Linux/Mac
source virtual/bin/activate

====== DEPENDENCIAS ======
pip install -r requirements.txt
```

## 💻 Uso

```bash
# Análisis básico
python PhoneOs.py +5491155667788

# Con exportación JSON
python PhoneOs.py +5491155667788 --json

# Con exportación CSV
python PhoneOs.py +5491155667788 --csv

# Con exportación HTML (reporte visual)
python PhoneOs.py +5491155667788 --html

# Análisis por lotes (batch)
python PhoneOs.py --batch "+5491155667788,+542945556684" --csv-output resultados.csv

# Cargar números desde CSV
python PhoneOs.py --csv-input numeros.csv --csv-output resultados.csv

# Filtrar por país (en análisis por lotes)
python PhoneOs.py --batch "+5491155667788,+542945556684" --country "Buenos Aires"

# Filtrar por operador (en análisis por lotes)
python PhoneOs.py --batch "+5491155667788,+542945556684" --carrier "Personal"

# Ver estadísticas globales
python PhoneOs.py --stats

# Ver historial de últimas búsquedas
python PhoneOs.py --history

# Limpiar caché local
python PhoneOs.py --clear-cache

# Ver ayuda completa
python PhoneOs.py -h
```

**O usa el lanzador para Windows:**
```powershell
.\run.bat +5491155667788
.\run.bat --stats
.\run.bat --batch "+5491155667788,+542945556684"
```

## 📤 Formatos de Salida

| Formato | Ejemplo |
|---------|---------|
| E.164 | `+5491155667788` |
| Internacional | `+54 9 11 5566-7788` |
| Nacional | `011 5566-7788` |

## � Ejemplos Avanzados

### Geolocalización con Mapa
```bash
python PhoneOs.py +5491155667788 --map
# Genera: outputs/5491155667788/mapa.html (mapa interactivo)
```

### OSINT de Emails
```bash
python PhoneOs.py +5491155667788 --email
# Genera: outputs/5491155667788/emails_osint.json
```

### Reporte PDF Profesional
```bash
python PhoneOs.py +5491155667788 --pdf
# Genera: outputs/5491155667788/reporte_profesional.pdf
```

### Análisis Completo (Todo)
```bash
python PhoneOs.py +5491155667788 --map --email --pdf --json --csv --html
# Genera: mapa.html, emails_osint.json, reporte_profesional.pdf, resultado.json, resultado.csv, reporte.html
```

### Dashboard Web Interactivo
```bash
python PhoneOs.py --web-server
# Abre: http://localhost:8000 (API REST + Interfaz gráfica)
```

### Análisis por Lotes
```bash
python PhoneOs.py --batch "+5491155667788,+542945556684,+34915551234" --csv-output "resultados.csv" --pdf
```

### Filtrar por País/Operador
```bash
python PhoneOs.py --batch "+5491155667788,+5491234567890,+34915551234" --country "Argentina"
python PhoneOs.py --batch "+5491155667788,+5491234567890" --carrier "Personal"
```

## 🔍 Ejemplo de Salida

```
── INPUT ──────────────────────────────
📥 Original     : +15551234567
🧼 Normalizado  : +15551234567
✔ Válido       : True

── ANÁLISIS ──────────────────────────────
🌍 País        : United States [HIGH]
📡 Operador    : Verizon [MEDIUM]
🕒 Zona horaria: America/New_York [MEDIUM]

── FORMATOS ──────────────────────────────
📞 E.164        : +15551234567
🌐 Internacional: +1 555-123-4567
🏠 Nacional     : (555) 123-4567
```

## 📊 Risk Score Explicado

El Risk Score (0-100) evalúa cada número:
- **0-30: BAJO** ✅ - Número válido con información completa
- **30-60: MEDIO** ⚠️ - Algún dato incompleto (operador desconocido)
- **60-100: ALTO** ❌ - Múltiples problemas o número inválido
- **100: CRÍTICO** 🚨 - Número completamente inválido

## 📁 Estructura de Archivos

```
outputs/
├── 5491155667788/
│   ├── resultado.json          # Análisis completo en JSON
│   ├── resultado.csv           # Resultado en CSV
│   ├── reporte.html            # Tabla HTML
│   ├── mapa.html               # Mapa interactivo (si --map)
│   ├── emails_osint.json       # OSINT de emails (si --email)
│   └── reporte_profesional.pdf # PDF profesional (si --pdf)
├── 542945556684/
│   └── ...
└── batch_reports/
    ├── batch_20260203_225212.csv
    └── resultados.csv
```

## ⚙️ Limitaciones

- No accede a datos en tiempo real ni privados
- La info de operador puede no reflejar portabilidad
- Basado en la librería `phonenumbers`
- Niveles de confianza heurísticos

## 🤝 Contribuciones

Forks y PRs bienvenidos. Mantén estándares éticos.