# EcoFlow STREAM für Home Assistant

Home-Assistant-Integration für **EcoFlow STREAM** Mikro-Wechselrichter. Die Geräte beantworten die
normale REST-Abfrage der EcoFlow-Cloud nicht, sondern senden ihre Werte nur per MQTT. Diese Integration
hält die MQTT-Verbindung offen (EcoFlow Open API) und legt Sensoren an. Home Assistant zeichnet den
Verlauf selbst auf. Keine zusätzlichen Python-Pakete nötig.

## Sensoren

| Sensor | Einheit |
|---|---|
| Grid feed-in power (Einspeiseleistung) | W |
| Solar input 2 power | W |
| Grid voltage (Netzspannung) | V |
| Inverter temperature | °C |

Die Sensoren erscheinen unter dem Gerät **EcoFlow STREAM**, z. B. `sensor.ecoflow_stream_grid_feed_in_power`.

## Installation über HACS

1. HACS → ⋮ → **Benutzerdefinierte Repositories** → URL dieses Repos eintragen, Kategorie **Integration**.
2. „EcoFlow STREAM“ installieren und Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „EcoFlow STREAM“.

Manuell: Ordner `custom_components/ecoflow_stream` nach `/config/custom_components/` kopieren.

## Zugangsdaten

Auf <https://developer.ecoflow.com> mit dem EcoFlow-Konto anmelden und einen **Access Key** und
**Secret Key** erzeugen. Die **Seriennummer** steht am Gerät und in der EcoFlow-App. Alle drei werden in
der Einrichtung abgefragt.

## Hinweise

- Laut Berichten sendet das Gerät ohne geöffnete EcoFlow-App teils nur selten neue Werte; die
  Verbindung wird bei Abbruch automatisch erneuert.
- Für den Tagesertrag in kWh: Helfer **Integral (Riemann-Summe)** auf den Einspeise-Sensor legen.
- `devcommandyt` in `custom_components/ecoflow_stream/manifest.json` durch den GitHub-Namen ersetzen.
