#!/usr/bin/env python3
"""
Phone OSINT Intelligence — Agregador OSINT Completo
Recolecta: Persona, Emails, Redes Sociales, Empresa, Breaches, Conexiones
"""

import requests
import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path
import re
from collections import defaultdict

# ========== CONFIGURACIÓN ==========
INTEL_DB = "phone_osint_intelligence.db"
CACHE_INTEL = "intel_cache.json"

# APIs públicas/mockeo
HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/"
GOOGLE_DORKS = [
    'phone:"{phone}"',
    '"{phone}"',
    'filetype:pdf "{phone}"',
]

# ========== BASE DE DATOS ==========
class IntelligenceDB:
    """Base de datos para correlacionar información OSINT"""
    
    def __init__(self, db_file=INTEL_DB):
        self.db_file = db_file
        self.init_db()
    
    def init_db(self):
        """Crear tablas si no existen"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Tabla: Personas
        c.execute('''CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            numero_principal TEXT UNIQUE,
            edad INTEGER,
            ubicacion TEXT,
            reputacion TEXT,
            empresa_id INTEGER,
            foto_url TEXT,
            verificado BOOLEAN,
            fecha_descubrimiento TIMESTAMP,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id)
        )''')
        
        # Tabla: Emails
        c.execute('''CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            persona_id INTEGER,
            dominio TEXT,
            tipo TEXT,
            verificado BOOLEAN,
            en_breach BOOLEAN,
            FOREIGN KEY(persona_id) REFERENCES personas(id)
        )''')
        
        # Tabla: Redes Sociales
        c.execute('''CREATE TABLE IF NOT EXISTS redes_sociales (
            id INTEGER PRIMARY KEY,
            plataforma TEXT,
            username TEXT,
            url TEXT,
            persona_id INTEGER,
            followers INTEGER,
            verificado BOOLEAN,
            FOREIGN KEY(persona_id) REFERENCES personas(id)
        )''')
        
        # Tabla: Empresas
        c.execute('''CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE,
            dominio TEXT,
            ubicacion TEXT,
            empleados INTEGER,
            rubro TEXT
        )''')
        
        # Tabla: Números Relacionados
        c.execute('''CREATE TABLE IF NOT EXISTS numeros_relacionados (
            id INTEGER PRIMARY KEY,
            numero_1 TEXT,
            numero_2 TEXT,
            relacion TEXT,
            fuerza REAL,
            UNIQUE(numero_1, numero_2)
        )''')
        
        # Tabla: Breaches
        c.execute('''CREATE TABLE IF NOT EXISTS breaches (
            id INTEGER PRIMARY KEY,
            email TEXT,
            nombre_breach TEXT,
            fecha_breach DATE,
            datos_afectados TEXT,
            fecha_descubrimiento TIMESTAMP
        )''')
        
        conn.commit()
        conn.close()
    
    def guardar_persona(self, data):
        """Guardar o actualizar persona"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        try:
            c.execute('''INSERT INTO personas 
                (nombre, numero_principal, edad, ubicacion, reputacion, foto_url, verificado, fecha_descubrimiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('nombre'),
                data.get('numero'),
                data.get('edad'),
                data.get('ubicacion'),
                data.get('reputacion', 'DESCONOCIDA'),
                data.get('foto'),
                data.get('verificado', False),
                datetime.now()
            ))
        except sqlite3.IntegrityError:
            # Actualizar si ya existe
            c.execute('''UPDATE personas SET 
                nombre=?, edad=?, ubicacion=?, reputacion=?, foto_url=?, verificado=?
                WHERE numero_principal=?
            ''', (
                data.get('nombre'),
                data.get('edad'),
                data.get('ubicacion'),
                data.get('reputacion'),
                data.get('foto'),
                data.get('verificado'),
                data.get('numero')
            ))
        
        conn.commit()
        conn.close()
    
    def guardar_email(self, numero, email, dominio, en_breach=False):
        """Guardar email asociado"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Obtener persona_id
        c.execute('SELECT id FROM personas WHERE numero_principal=?', (numero,))
        result = c.fetchone()
        persona_id = result[0] if result else None
        
        if persona_id:
            try:
                c.execute('''INSERT INTO emails 
                    (email, persona_id, dominio, tipo, en_breach)
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, persona_id, dominio, 'personal', en_breach))
            except sqlite3.IntegrityError:
                c.execute('UPDATE emails SET en_breach=? WHERE email=?', (en_breach, email))
        
        conn.commit()
        conn.close()
    
    def guardar_red_social(self, numero, plataforma, username, url, followers=0):
        """Guardar red social"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('SELECT id FROM personas WHERE numero_principal=?', (numero,))
        result = c.fetchone()
        persona_id = result[0] if result else None
        
        if persona_id:
            c.execute('''INSERT OR REPLACE INTO redes_sociales 
                (plataforma, username, url, persona_id, followers, verificado)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (plataforma, username, url, persona_id, followers, False))
        
        conn.commit()
        conn.close()
    
    def guardar_breach(self, email, nombre_breach, fecha_breach):
        """Guardar breach encontrado"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''INSERT OR IGNORE INTO breaches 
            (email, nombre_breach, fecha_breach, fecha_descubrimiento)
            VALUES (?, ?, ?, ?)
        ''', (email, nombre_breach, fecha_breach, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def obtener_perfil_completo(self, numero):
        """Obtener todo lo conocido sobre una persona"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Persona base
        c.execute('SELECT * FROM personas WHERE numero_principal=?', (numero,))
        persona = c.fetchone()
        
        if not persona:
            return None
        
        persona_id = persona[0]
        resultado = {
            'persona': {
                'id': persona_id,
                'nombre': persona[1],
                'numero': persona[2],
                'edad': persona[3],
                'ubicacion': persona[4],
                'reputacion': persona[5],
                'empresa_id': persona[6],
                'foto': persona[7],
                'verificado': persona[8]
            },
            'emails': [],
            'redes_sociales': [],
            'breaches': [],
            'empresa': None,
            'numeros_relacionados': []
        }
        
        # Emails
        c.execute('SELECT email, dominio, en_breach FROM emails WHERE persona_id=?', (persona_id,))
        resultado['emails'] = [{'email': row[0], 'dominio': row[1], 'en_breach': row[2]} for row in c.fetchall()]
        
        # Redes sociales
        c.execute('SELECT plataforma, username, url, followers FROM redes_sociales WHERE persona_id=?', (persona_id,))
        resultado['redes_sociales'] = [{'plataforma': row[0], 'username': row[1], 'url': row[2], 'followers': row[3]} for row in c.fetchall()]
        
        # Breaches
        c.execute('SELECT nombre_breach, fecha_breach FROM breaches WHERE email IN (SELECT email FROM emails WHERE persona_id=?)', (persona_id,))
        resultado['breaches'] = [{'nombre': row[0], 'fecha': row[1]} for row in c.fetchall()]
        
        # Empresa
        if persona[6]:
            c.execute('SELECT * FROM empresas WHERE id=?', (persona[6],))
            empresa = c.fetchone()
            if empresa:
                resultado['empresa'] = {
                    'nombre': empresa[1],
                    'dominio': empresa[2],
                    'ubicacion': empresa[3],
                    'empleados': empresa[4]
                }
        
        # Números relacionados
        c.execute('''SELECT numero_1, numero_2, relacion, fuerza FROM numeros_relacionados 
            WHERE numero_1=? OR numero_2=?''', (numero, numero))
        resultado['numeros_relacionados'] = [{'numero': row[1] if row[0] == numero else row[0], 'relacion': row[2], 'fuerza': row[3]} for row in c.fetchall()]
        
        conn.close()
        return resultado


# ========== MÓDULO 1: BÚSQUEDA INVERSA ==========
class ReversePhoneLookup:
    """Busca nombre, ubicación, foto desde número"""
    
    @staticmethod
    def buscar_nombre_y_ubicacion(numero, pais=None):
        """Búsqueda básica de nombre y ubicación"""
        # Mockeo de datos realistas (en producción usaría TrueCaller API)
        datos_simulados = {
            '+5491155667788': {
                'nombre': 'Juan García Pérez',
                'ubicacion': 'Buenos Aires, Argentina',
                'edad': 34,
                'tipo': 'MOBILE',
                'reputacion': 'CONFIABLE'
            },
            '+34915551234': {
                'nombre': 'María López García',
                'ubicacion': 'Madrid, España',
                'edad': 28,
                'tipo': 'FIXED_LINE',
                'reputacion': 'DESCONOCIDA'
            },
            '+12125551234': {
                'nombre': 'John Smith',
                'ubicacion': 'New York, USA',
                'edad': 45,
                'tipo': 'MOBILE',
                'reputacion': 'CONFIABLE'
            }
        }
        
        return datos_simulados.get(numero, {
            'nombre': 'Desconocido',
            'ubicacion': pais or 'No determinado',
            'edad': None,
            'tipo': 'DESCONOCIDO',
            'reputacion': 'SIN DATOS'
        })
    
    @staticmethod
    def google_dorks_busqueda(numero):
        """Simula búsqueda en Google con dorks"""
        # En producción: usar selenium/scraping de Google
        print(f"  [Busqueda Google Dorks para {numero}...]")
        return {
            'resultados': 3,
            'menciones': [
                {'titulo': 'Perfil LinkedIn', 'url': 'linkedin.com/in/...'},
                {'titulo': 'Directorio empresarial', 'url': 'empresas.com/...'},
                {'titulo': 'Red social', 'url': 'facebook.com/...'}
            ]
        }


# ========== MÓDULO 2: RECOLECTOR DE EMAILS ==========
class EmailFinder:
    """Encuentra todos los emails asociados a una persona"""
    
    @staticmethod
    def buscar_emails_por_nombre(nombre, dominio=None):
        """Busca emails usando HunterIO API (mockeo)"""
        # Emails de ejemplo basados en el nombre
        partes = nombre.lower().split()
        emails_base = []
        
        if len(partes) >= 2:
            primer_nombre = partes[0]
            apellido = partes[-1]
            
            emails_base = [
                f"{primer_nombre}.{apellido}@gmail.com",
                f"{primer_nombre}{apellido}@hotmail.com",
                f"{primer_nombre}@outlook.com",
                f"{primer_nombre}.{apellido}@yahoo.com",
            ]
        
        if dominio:
            emails_base.extend([
                f"{primer_nombre}@{dominio}",
                f"{primer_nombre}.{apellido}@{dominio}",
                f"{apellido}@{dominio}",
            ])
        
        return emails_base
    
    @staticmethod
    def verificar_breach(email):
        """Verifica si email está en breaches (HIBP API)"""
        # Mockeo de breach check
        emails_con_breach = {
            'juan.garcia@gmail.com': ['LinkedIn 2021', 'Facebook 2019'],
            'maria.lopez@gmail.com': ['Adobe 2013', 'Equifax 2017'],
            'john.smith@outlook.com': []
        }
        
        return emails_con_breach.get(email, [])


# ========== MÓDULO 3: SCRAPER DE REDES SOCIALES ==========
class SocialMediaFinder:
    """Busca perfiles en redes sociales (usando Sherlock pattern)"""
    
    REDES_SOCIALES = {
        'Facebook': 'https://facebook.com/{username}',
        'Instagram': 'https://instagram.com/{username}',
        'Twitter': 'https://twitter.com/{username}',
        'TikTok': 'https://tiktok.com/@{username}',
        'LinkedIn': 'https://linkedin.com/in/{username}',
        'GitHub': 'https://github.com/{username}',
        'YouTube': 'https://youtube.com/@{username}',
        'Telegram': 'https://t.me/{username}',
        'Twitch': 'https://twitch.tv/{username}',
        'Reddit': 'https://reddit.com/u/{username}',
    }
    
    @staticmethod
    def buscar_perfiles(nombre, email_base=None):
        """Simula búsqueda Sherlock de perfiles"""
        usernames_posibles = [
            nombre.lower().replace(' ', ''),
            nombre.lower().replace(' ', '.'),
            nombre.lower().replace(' ', '_'),
            email_base.split('@')[0] if email_base else None,
        ]
        
        # Mockeo de perfiles encontrados
        perfiles_encontrados = []
        
        # Simulación de búsqueda
        redes_disponibles = ['Facebook', 'Instagram', 'Twitter', 'LinkedIn', 'GitHub', 'YouTube']
        
        for red in redes_disponibles:
            for username in usernames_posibles:
                if username and len(username) > 3:
                    # Probabilidad realista de que exista
                    if hash(f"{red}{username}") % 3 == 0:  # ~33% probabilidad
                        url = SocialMediaFinder.REDES_SOCIALES[red].format(username=username)
                        perfiles_encontrados.append({
                            'plataforma': red,
                            'username': username,
                            'url': url,
                            'followers': hash(username) % 10000 + 100 if red != 'GitHub' else None,
                            'verificado': False
                        })
        
        return perfiles_encontrados


# ========== MÓDULO 4: INTELIGENCIA DE EMPRESA ==========
class CompanyIntelligence:
    """Recolecta información de empresas asociadas"""
    
    @staticmethod
    def buscar_empresa(nombre_empresa, numero=None):
        """Busca información de empresa (mockeo de Apollo.io, Clearbit)"""
        # Datos simulados
        empresas_db = {
            'TechCorp': {
                'nombre': 'TechCorp SRL',
                'dominio': 'techcorp.com.ar',
                'ubicacion': 'Buenos Aires, Argentina',
                'empleados': 45,
                'rubro': 'Software/IT',
                'descripcion': 'Empresa de desarrollo de software y consultoría',
                'linkedin': 'linkedin.com/company/techcorp',
                'fundacion': 2018
            }
        }
        
        return empresas_db.get(nombre_empresa, {
            'nombre': nombre_empresa,
            'dominio': f"{nombre_empresa.lower()}.com",
            'ubicacion': 'Desconocida',
            'empleados': None,
            'rubro': 'Desconocido'
        })
    
    @staticmethod
    def buscar_empleados(nombre_empresa):
        """Busca empleados de una empresa"""
        # Mockeo de empleados
        return [
            {'nombre': 'Juan García', 'puesto': 'CEO', 'linkedin': 'linkedin.com/in/jgarcia'},
            {'nombre': 'María López', 'puesto': 'CTO', 'linkedin': 'linkedin.com/in/mlopez'},
            {'nombre': 'Carlos Ruiz', 'puesto': 'CFO', 'linkedin': 'linkedin.com/in/cruiz'},
        ]


# ========== MÓDULO 5: ANÁLISIS DE BREACHES & REPUTACIÓN ==========
class BreachAnalysis:
    """Verifica breaches y analiza reputación"""
    
    @staticmethod
    def check_breaches_completo(emails):
        """Verifica múltiples emails en breaches"""
        resultados = {}
        
        for email in emails:
            # Mockeo de HIBP API
            breaches = EmailFinder.verificar_breach(email)
            resultados[email] = {
                'en_breach': len(breaches) > 0,
                'breaches': breaches,
                'cantidad': len(breaches)
            }
        
        return resultados
    
    @staticmethod
    def analizar_reputacion(datos_persona, breaches):
        """Calcula score de reputación"""
        score = 100
        razones = []
        
        # Penalizaciones
        if breaches:
            score -= 20
            razones.append(f"Email en {len(breaches)} breaches")
        
        if 'desconocido' in str(datos_persona).lower():
            score -= 15
            razones.append("Información limitada")
        
        if score < 40:
            nivel = "[ALTO RIESGO]"
        elif score < 70:
            nivel = "[RIESGO MEDIO]"
        else:
            nivel = "[BAJO RIESGO]"
        
        return {
            'score': max(0, score),
            'nivel': nivel,
            'razones': razones
        }


# ========== ORQUESTADOR PRINCIPAL ==========
class IntelligenceOrchestrator:
    """Coordina todos los módulos de OSINT"""
    
    def __init__(self):
        self.db = IntelligenceDB()
        self.reverse_lookup = ReversePhoneLookup()
        self.email_finder = EmailFinder()
        self.social_finder = SocialMediaFinder()
        self.company_intel = CompanyIntelligence()
        self.breach_analysis = BreachAnalysis()
    
    def investigar_completo(self, numero, pais=None):
        """Investigación OSINT completa en 1 número"""
        resultado = {
            'numero': numero,
            'timestamp': datetime.now().isoformat(),
            'personas': {},
            'emails': [],
            'redes_sociales': [],
            'empresa': None,
            'breaches': {},
            'reputacion': {}
        }
        
        print(f"\n[INVESTIGACION COMPLETA]: {numero}")
        print("=" * 60)
        
        # 1. BÚSQUEDA INVERSA
        print("\n[1] BUSQUEDA INVERSA...")
        persona = self.reverse_lookup.buscar_nombre_y_ubicacion(numero, pais)
        resultado['personas'] = persona
        print(f"   * Nombre: {persona.get('nombre')}")
        print(f"   * Ubicación: {persona.get('ubicacion')}")
        print(f"   * Edad aprox: {persona.get('edad')}")
        
        # Guardar en DB
        self.db.guardar_persona({
            'numero': numero,
            'nombre': persona.get('nombre'),
            'edad': persona.get('edad'),
            'ubicacion': persona.get('ubicacion'),
            'reputacion': persona.get('reputacion')
        })
        
        # Google Dorks
        print("\n   Busqueda en Google...")
        dorks = self.reverse_lookup.google_dorks_busqueda(numero)
        
        # 2. RECOLECTOR DE EMAILS
        print("\n[2] RECOLECTOR DE EMAILS...")
        nombre = persona.get('nombre', '')
        emails = self.email_finder.buscar_emails_por_nombre(nombre)
        resultado['emails'] = emails
        print(f"   * Encontrados {len(emails)} emails posibles:")
        for email in emails[:5]:
            print(f"     + {email}")
        
        # 3. BUSCAR EN REDES SOCIALES
        print("\n[3] BUSQUEDA EN REDES SOCIALES...")
        perfiles = self.social_finder.buscar_perfiles(nombre, emails[0] if emails else None)
        resultado['redes_sociales'] = perfiles
        print(f"   * Encontrados {len(perfiles)} perfiles:")
        for perfil in perfiles:
            print(f"     + {perfil['plataforma']}: {perfil['username']}")
            self.db.guardar_red_social(numero, perfil['plataforma'], perfil['username'], perfil['url'], perfil.get('followers', 0))
        
        # 4. INTELIGENCIA DE EMPRESA
        print("\n[4] BUSQUEDA DE EMPRESA...")
        # Simulación: asumir que tiene empresa
        empresa = self.company_intel.buscar_empresa('TechCorp', numero)
        resultado['empresa'] = empresa
        print(f"   * Empresa: {empresa.get('nombre')}")
        print(f"   * Dominio: {empresa.get('dominio')}")
        print(f"   * Empleados: {empresa.get('empleados')}")
        
        # 5. ANÁLISIS DE BREACHES
        print("\n[5] ANALISIS DE BREACHES...")
        breaches = self.breach_analysis.check_breaches_completo(emails)
        resultado['breaches'] = breaches
        
        total_breaches = sum(b['cantidad'] for b in breaches.values())
        print(f"   * Emails verificados: {len(emails)}")
        print(f"   * Breaches encontrados: {total_breaches}")
        
        for email, info in breaches.items():
            if info['en_breach']:
                print(f"     [ALERTA] {email}: {', '.join(info['breaches'])}")
                for breach in info['breaches']:
                    self.db.guardar_breach(email, breach, '2000-01-01')
                    self.db.guardar_email(numero, email, email.split('@')[1], True)
            else:
                self.db.guardar_email(numero, email, email.split('@')[1], False)
        
        # 6. REPUTACIÓN FINAL
        print("\n[6] ANALISIS DE REPUTACION...")
        reputacion = self.breach_analysis.analizar_reputacion(persona, breaches)
        resultado['reputacion'] = reputacion
        print(f"   * Score: {reputacion['score']}/100")
        print(f"   * Nivel: {reputacion['nivel']}")
        if reputacion['razones']:
            print(f"   * Razones:")
            for razon in reputacion['razones']:
                print(f"     - {razon}")
        
        print("\n" + "=" * 60)
        
        return resultado
    
    def exportar_json_inteligencia(self, resultado, output_path):
        """Exporta resultado a JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        print(f"✔ Exportado a {output_path}")
    
    def obtener_perfil_360(self, numero):
        """Retorna perfil completo desde BD"""
        return self.db.obtener_perfil_completo(numero)


# Instancia global
intelligence = IntelligenceOrchestrator()
