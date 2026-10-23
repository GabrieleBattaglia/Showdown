# MESS, Manageriale e Simulatore Showdown

Un gioco gestionale dello showdown, il tennistavolo per ciechi, pensato da un giocatore cieco. Concepito il 13 aprile 2015, portato in Python nel 2020, rifatto da capo nel 2026 con un'interfaccia a finestra accessibile.

L'Italia dello showdown è piena di giocatori generati a caso, ciascuno con nome, aspetto fisico descritto a parole, comune di provenienza e 26 caratteristiche tecniche e fisiche. Tu fondi una o più polisportive, tesseri atleti convincendoli con la tua gloria, li alleni con il tuo staff e li porti ai tornei, fino al Campionato italiano. Accanto a te vivono le polisportive guidate dal computer, e il mondo scorre con l'orologio vero: ogni 8 ore reali passa un giorno simulato, i giocatori invecchiano, si ritirano, diventano allenatori e lasciano il posto a nuove leve.

## Scaricare e installare

MESS gira su Windows 10 e 11 a 64 bit. L'ultima versione sta nella pagina delle release su GitHub: https://github.com/GabrieleBattaglia/Showdown/releases

- **Con l'installatore, MESS-Setup:** chiede di accettare la licenza GPL 3 e installa MESS nella tua cartella dei programmi, senza permessi di amministratore. Alla disinstallazione chiede se cancellare anche la cartella Mondo; una cartella del mondo scelta altrove resta com'è.
- **Con lo zip, MESS.zip:** si scompatta in una cartella dove puoi scrivere, mai in Programmi, perché di serie il mondo si salva nella cartella Mondo accanto al programma.

Il programma non è firmato, quindi al primo avvio Windows può mostrare l'avviso di SmartScreen: Altre informazioni, poi Esegui comunque.

All'avvio MESS controlla se c'è una versione nuova e propone di installarla: l'aggiornamento salva il mondo, sostituisce il programma e lo riapre.

## Come si gioca

Si apre la finestra con la vista, dove si leggono schede, elenchi e notizie, e la barra di stato, con F7, che dice in poche righe la data, la polisportiva attiva e gli eventi. Ogni comando sta in un menu e ha il suo suono. F1 dà la guida ai comandi, F2 le novità, Maiusc+F1 apre il manuale completo nel browser.

Le partite seguono il regolamento IBSA dello showdown, e si ascoltano dal vivo, con i suoni della pallina, dei colpi e dell'arbitro che si muovono sul tavolo, oppure in differita. Ci sono la sala allenamento, il mercato, i contratti, lo staff con gli allenatori, i tornei a calendario con la Classifica nazionale e il Campionato italiano, le sfide fra polisportive e la Coppa delle polisportive, l'albo d'oro e le statistiche nazionali.

## Aiuto

- Il manuale, con Maiusc+F1, spiega ogni menu, ogni tasto e le regole del gioco.
- Nel menu Aiuto, Entra al PUB prepara la mail per iscriversi alla lista di supporto degli utenti, e Chiedi aiuto al PUB prepara quella con la domanda e le informazioni sul computer.
- I problemi si segnalano anche come issue su GitHub: https://github.com/GabrieleBattaglia/Showdown/issues

Un errore imprevisto si annota in MESS - Errori.log, accanto al programma: è il file da allegare quando chiedi aiuto.

## Accessibilità

MESS è pensato per lo screen reader e il display braille: testi discorsivi, senza separatori grafici né tabelle allineate a colonne, finestre massimizzate, un suono per ogni azione e la cronaca della partita che si può leggere in automatico alla sintesi o al display braille.

## Dai sorgenti

Serve Python 3.14, con le librerie di requirements.txt, e GBUtils, la libreria condivisa del parco software di IZ4APU, che non sta su PyPI e va clonata a parte, con la sua cartella in PYTHONPATH:

    git clone https://github.com/GabrieleBattaglia/GBUtils.git
    pip install -r requirements.txt
    python Showdown.py

Le prove stanno nella cartella tests, con pytest. La cartella strumenti contiene i banchi e le tarature del piano di sviluppo, e i loro rapporti. Il pacchetto si compila con PyInstaller dalla ricetta MESS.spec, poi zip_maker.py prepara lo zip per l'aggiornamento automatico e setup_maker.py l'installatore con Inno Setup 6.

## Dati

La cartella dati contiene le collezioni di nomi e cognomi, un file di testo per collezione e una voce per riga; il vocabolario delle descrizioni fisiche, vocabolario.json; luoghi_italiani.json, 1.291 comuni italiani con provincia, regione e abitanti, da cui si estraggono la provenienza di giocatori e allenatori e la sede delle polisportive; i modelli dei tornei e le loro formule.

Il mondo si salva nella cartella del mondo: di serie è la cartella Mondo accanto al programma, e con Cartella del mondo, nel menu Impostazioni, se ne sceglie un'altra, per esempio in Dropbox, per ritrovare il mondo su ogni computer. Lì stanno il file compresso mess_mondo.json.gz, con la copia di sicurezza mess_mondo.json.gz.bak, che si salva da solo a ogni avanzamento e a ogni operazione sulle polisportive; le impostazioni, mess_impostazioni.json; i modelli e le formule dei tornei che si possono cambiare con gli editor; le cronache salvate, nella cartella cronache; e il registro delle vecchie glorie, vecchie_glorie.log. Il file del mondo è firmato: una modifica fatta a mano viene scoperta, e il gioco riprende dalla copia. Accanto al programma restano i registri degli errori e, se la cartella del mondo non è quella di serie, mess_cartella_del_mondo.json, che ricorda dove sta.

## Licenza

MESS è software libero, con licenza GNU GPL versione 3: vedi il file LICENSE.

## Autori

Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
