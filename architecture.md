# Stock Portfolio Webapp - Architektur Dokumentation

## Übersicht

Die Stock Portfolio Webapp ist eine Anwendung zum Verfolgen und Verwalten von Aktienportfolios. Die Anwendung ermöglicht es Benutzern, ihre Aktien zu verfolgen, historische Daten zu visualisieren, automatisierte Handelsaufträge zu erstellen und KI-gestützte Einblicke in ihre Investments zu erhalten.

## Anforderungen

### Funktionale Anforderungen

1. **Benutzerauthentifizierung und -autorisierung**
   - Registrierung und Login für Benutzer
   - Sichere Speicherung von Benutzeranmeldedaten
   - Authentifizierung über JWT-Token

2. **Portfolio-Management**
   - Hinzufügen, Bearbeiten und Löschen von Aktienpositionen
   - Anzeigen von Portfolio-Zusammenfassungen mit aktuellen Werten
   - Berechnung von Gewinn/Verlust und Performance-Metriken

3. **Aktiendaten**
   - Abrufen von aktuellen und historischen Aktienkursen
   - Anzeigen von Dividendeninformationen
   - Visualisierung von Kursverläufen mit interaktiven Charts

4. **Handelsaufträge**
   - Erstellen von automatisierten Kauf- und Verkaufsaufträgen
   - Verfolgung des Status von Aufträgen
   - Ausführung von Aufträgen basierend auf Marktbedingungen

5. **KI-Chatbot**
   - Beantwortung von Fragen zu Aktien und zum Portfolio
   - Bereitstellung von Einblicken und Analysen
   - Erhaltung des Gesprächskontexts

### Nicht-funktionale Anforderungen

1. **Skalierbarkeit**
   - Containerisierte Anwendung für einfache Skalierung
   - Modulare Architektur für unabhängige Komponentenskalierung

2. **Wartbarkeit**
   - Klare Trennung von Verantwortlichkeiten durch modularen Aufbau
   - Vollständige Dokumentation der APIs
   - Testabdeckung für kritische Komponenten

3. **Performance**
   - Schnelle Antwortzeiten für API-Anfragen (<500ms)
   - Effiziente Datenbankanfragen durch Verwendung von Indizes
   - Caching für häufig abgerufene Daten

4. **Sicherheit**
   - Sichere Passwort-Hashing-Mechanismen
   - JWT-basierte Authentifizierung
   - Schutz vor gängigen Angriffen (CSRF, XSS, SQL-Injection)

5. **Verfügbarkeit**
   - 99.9% Uptime-Ziel
   - Health-Check-Endpunkte für Monitoring
   - Robustes Fehlerhandling

## Architektur

Die Anwendung verwendet eine moderne, modulare Architektur mit klarer Trennung zwischen Frontend und Backend.

### Systemarchitektur (Übersicht)

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│               │      │               │      │               │
│    Frontend   │◄────►│    Backend    │◄────►│    Database   │
│   (Streamlit) │      │   (FastAPI)   │      │  (PostgreSQL) │
│               │      │               │      │               │
└───────────────┘      └───────────────┘      └───────────────┘
                              │
                              ▼
                       ┌───────────────┐
                       │  External APIs │
                       │  (Stock Data)  │
                       │               │
                       └───────────────┘
```

### Backend-Architektur

Das Backend verwendet eine Schichtenarchitektur:

```
┌─────────────────────────────────────────────────────┐
│                      API Layer                      │
│                                                     │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Auth    │  │   Portfolio  │  │    Stocks    │  │
│  └───────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────┐
│                    Service Layer                    │
│                                                     │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ AuthSvc   │  │PortfolioSvc  │  │  StockSvc    │  │
│  └───────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────┐
│                  Repository Layer                   │
│                                                     │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  UserRepo │  │ PositionRepo │  │  OrderRepo   │  │
│  └───────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────┐
│                     Data Layer                      │
│                                                     │
│                   PostgreSQL DB                     │
└─────────────────────────────────────────────────────┘
```

### Technologie-Stack

1. **Frontend**
   - Streamlit: Für interaktive UI-Komponenten und Visualisierungen
   - Plotly: Für interaktive Diagramme und Visualisierungen
   - Pandas: Für Datenmanipulation und -analyse

2. **Backend**
   - FastAPI: Für schnelle, asynchrone API-Entwicklung
   - SQLAlchemy: Als ORM für Datenbankoperationen
   - Pydantic: Für Datenschema-Validierung und -konvertierung
   - JWT: Für Authentifizierung und Sicherheit

3. **Datenbank**
   - PostgreSQL: Relationale Datenbank für persistente Datenspeicherung
   - Alembic: Für Datenbank-Migrations-Management

4. **Deployment**
   - Docker: Für Containerisierung der Anwendung
   - Docker Compose: Für die Orchestrierung der Container-Umgebung

### Datenmodell

```
┌───────────┐          ┌────────────┐          ┌───────────┐
│   User    │          │  Position  │          │   Order   │
├───────────┤          ├────────────┤          ├───────────┤
│ id        │◄─────┐   │ id         │          │ id        │
│ username  │      │   │ user_id    │────┐     │ user_id   │
│ password  │      └───│ ticker     │    │     │ ticker    │
│ created_at│          │ shares     │    └─────│ order_type│
└───────────┘          │ entry_price│          │ price     │
                      │ purchase_dt│          │ quantity  │
                      └────────────┘          │ status    │
                                             │ created_at│
                                             │ executed_at│
                                             └───────────┘
```

## Deploymentstrategie

Die Anwendung ist vollständig containerisiert und verwendet Docker Compose für das Deployment. Dies ermöglicht eine einfache Skalierung und Verwaltung der Anwendungskomponenten.

### Container-Struktur

```
┌───────────────────────────────────────────────────┐
│                Docker Compose Setup               │
│                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Frontend  │  │   Backend   │  │  Database  │ │
│  │  Container  │  │  Container  │  │ Container  │ │
│  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                   │
└───────────────────────────────────────────────────┘
```

### Deployment-Prozess

1. **Lokale Entwicklung**
   - Entwicklung mit Docker Compose für konsistente Umgebungen
   - Hot-Reload für schnelle Iteration während der Entwicklung

2. **Testing**
   - Automatisierte Tests mit Pytest
   - Integration Tests für API-Endpunkte
   - Container-Tests für Deployment-Validierung

3. **Staging und Produktion**
   - Docker Compose für einfaches Deployment
   - Umgebungsvariablen für Konfiguration verschiedener Umgebungen
   - Gesundheitsprüfungen für Überwachung der Anwendungskomponenten

### Skalierung

Die Anwendung kann horizontal skaliert werden, indem mehrere Instanzen des Backend-Containers bereitgestellt werden. Ein Load Balancer kann hinzugefügt werden, um den Verkehr auf die verschiedenen Instanzen zu verteilen.

## Sicherheit

1. **Authentifizierung**
   - JWT-basiertes Authentifizierungssystem
   - Sichere Passwort-Hashing mit bcrypt
   - Token-Ablauf und -Erneuerung

2. **Datensicherheit**
   - Parameter-Validierung für alle API-Anfragen
   - Schutz vor SQL-Injection durch ORM
   - CORS-Konfiguration für API-Zugriff

## Monitoring und Logging

1. **Health Checks**
   - Endpunkt für Anwendungsgesundheit
   - Datenbankverbindungsprüfungen
   - Externe API-Verfügbarkeitsprüfungen

2. **Logging**
   - Strukturiertes Logging für alle Anwendungsebenen
   - Fehlerprotokollierung und -verfolgung
   - Leistungsmetriken für kritische Operationen

## Fazit

Die Stock Portfolio Webapp bietet eine moderne, modulare und skalierbare Architektur, die den definierten funktionalen und nicht-funktionalen Anforderungen entspricht. Die klare Trennung von Verantwortlichkeiten und die Verwendung von Best Practices in der Softwareentwicklung gewährleisten Wartbarkeit, Skalierbarkeit und Erweiterbarkeit für zukünftige Funktionen.
