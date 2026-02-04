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

## 📁 Archivos Generados

- `phone_osint.log` - Registro de todas las consultas
- `phone_osint_cache.pkl` - Caché local en pickle
- `phone_osint_history.json` - Historial de búsquedas
- `phone_osint_stats.json` - Estadísticas globales
- `phone_osint_output.*` - Exportaciones (JSON/CSV/HTML)

## ⚙️ Limitaciones

- No accede a datos en tiempo real ni privados
- La info de operador puede no reflejar portabilidad
- Basado en la librería `phonenumbers`
- Niveles de confianza heurísticos

## 🤝 Contribuciones

Forks y PRs bienvenidos. Mantén estándares éticos.