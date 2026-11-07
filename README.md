# ROMA ROMA ROMA 🟡🔴

Integrazione per Home Assistant per tifosi dell'**AS Roma**:

- 📅 **calendario delle partite** sempre aggiornato (Serie A, Champions/Europa League, Coppa Italia…);
- 📱 **avviso sul telefono** prima del calcio d'inizio (di default 30 minuti prima);
- 💡🎵 **spettacolo di luci giallorosse** prima della partita (di default 10 minuti prima): le tue luci diventano **rosse** e **gialle** e "respirano" a tempo con **"Roma Roma Roma"** di Antonello Venditti, mentre la canzone suona sui tuoi altoparlanti.

La squadra (AS Roma), la canzone e i colori sono fissi: tu scegli solo le tue luci, i tuoi altoparlanti e il tuo telefono.

> *English: Home Assistant integration for AS Roma fans: always up-to-date fixtures calendar, phone alert before kick-off and a red & yellow light show synced to "Roma Roma Roma".*

## Installazione (HACS)

1. HACS → menu ⋮ → **Repository personalizzati** → aggiungi `https://github.com/Elleukappa/roma-roma-roma`, categoria **Integrazione**.
2. Cerca **ROMA ROMA ROMA** e installa.
3. Riavvia Home Assistant.
4. **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → ROMA ROMA ROMA**.

Installazione manuale: copia `custom_components/roma_roma_roma` nella cartella `config/custom_components/` e riavvia.

## La canzone (importante)

Per motivi di **diritto d'autore il file mp3 NON è incluso**. Usa una tua copia legittima:

1. **Media → Media locali → Carica** il file e chiamalo esattamente
   `Antonello Venditti - Roma Roma Roma.mp3`
   (oppure, durante la configurazione, indica il tuo percorso `media-source://...`).
2. Lo spettacolo è calcolato sulla versione in studio da **3:11** (circa 77 battiti al minuto, 244 battute). Con versioni diverse (live, remix) la sincronia non sarà precisa.

## Configurazione

| Passo | Opzione | Descrizione |
|---|---|---|
| Luci | Luci rosse / Luci gialle | Una o più luci a colori per ciascun colore |
| | Prese da accendere prima | Facoltativo: la presa smart che alimenta le lampade (si attende che le luci tornino disponibili) |
| | Luminosità minima/massima | Escursione dell'effetto (default 10–100 %) |
| Canzone | Lettori | Altoparlanti, Cast, Music Assistant… (facoltativo) |
| | File canzone | Default `media-source://media_source/local/Antonello Venditti - Roma Roma Roma.mp3` |
| | Compensazione ritardo | Default 0,5 s: aumenta se le luci sono in ritardo sulla musica |
| Avvisi | Telefoni | Dispositivi con l'app Home Assistant (Android/iOS) |
| | Minuti prima | Avviso (default 30) e spettacolo (default 10) |
| | Persone / quando | Avvia lo spettacolo solo se qualcuno è in casa, anche se la posizione è sconosciuta, oppure sempre |
| | Solo Serie A | Ignora le coppe |

Tutto si può cambiare dopo da **Configura** sull'integrazione.

## Entità

| Entità | Cosa fa |
|---|---|
| `calendar.roma_roma_roma_partite` | Tutte le partite (utilizzabile anche nei trigger "calendario" delle tue automazioni) |
| `sensor.roma_roma_roma_prossima_partita` | Data/ora del prossimo calcio d'inizio, con avversario, competizione, stadio |
| `sensor.roma_roma_roma_prossimo_spettacolo` | Quando partirà il prossimo spettacolo |
| `switch.roma_roma_roma_avviso_sul_telefono` | Attiva/disattiva gli avvisi |
| `switch.roma_roma_roma_spettacolo_luci_e_inno` | Attiva/disattiva lo spettacolo |
| `button.roma_roma_roma_avvia_spettacolo_ora` | Prova subito luci e canzone |
| `button.roma_roma_roma_ferma_spettacolo` | Ferma lo spettacolo |
| `button.roma_roma_roma_notifica_di_prova` | Invia la data della prossima partita al telefono |

(Gli ID possono variare in base alla lingua di Home Assistant.)

## Servizi

- `roma_roma_roma.start_show` — `play_song` (default `true`), `offset` (s). Esempio con un comando vocale:

  ```yaml
  triggers:
    - trigger: conversation
      command: "forza roma"
  actions:
    - action: roma_roma_roma.start_show
  ```
- `roma_roma_roma.stop_show`
- `roma_roma_roma.test_notification`

## Come funziona lo spettacolo

La canzone è stata analizzata una volta sola (battute, bassi e volume) e la "mappa" è inclusa nell'integrazione (`beatmap.json`). A ogni battuta le luci rosse e gialle si alternano: chi guida sale in base a bassi e volume, l'altra resta soffusa; sui colpi più forti dei ritornelli si accendono entrambe al massimo. Ogni comando è agganciato all'orario assoluto di inizio canzone, quindi non accumula ritardo. Alla fine le luci restano accese rosse e gialle.

Consigli: lampadine a colori recenti (Matter, Zigbee, Wi-Fi locali) rispondono meglio; le lampadine cloud possono essere lente.

## Fonti e note

- Calendario: [fixtur.es](https://fixtur.es) (feed ICS pubblico, aggiornato ogni 6 ore).
- Progetto **non ufficiale**, non affiliato né approvato da AS Roma S.p.A. Marchi e brani appartengono ai rispettivi titolari.

## Licenza

MIT
