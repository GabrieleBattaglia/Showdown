# MESS, Manageriale e Simulatore Showdown

Un gioco gestionale dello showdown, il tennistavolo per ciechi, pensato da un giocatore cieco. Concepito il 13 aprile 2015 e portato in Python nel 2020.

Il mondo contiene giocatori generati a caso, ciascuno con nome, aspetto fisico descritto a parole e 26 caratteristiche tecniche e fisiche. Tu apri una o più polisportive, tesseri atleti convincendoli con la tua gloria, li alleni e organizzi partite simulate punto per punto. Accanto a te vivono polisportive guidate dal computer, e il mondo scorre con l'orologio vero: ogni 8 ore reali passa un giorno simulato, i giocatori invecchiano, si ritirano e lasciano il posto a nuove leve.

## Stato del progetto

MESS è in fase di rifacimento. Il lavoro segue le tappe del file `piano_di_sviluppo.txt`, che elenca i problemi del vecchio programma, le decisioni prese e l'ordine dei lavori. Il punto d'arrivo è la versione 2.0.0, con un'interfaccia a finestra accessibile.

Dalla versione 1.16.0 il gioco si apre in una finestra, da qualunque cartella, con:

    python Showdown.py

Nella finestra si consulta il mondo, con schede, diari di giocatori e polisportive, elenchi, classifiche, statistiche, ricerche e il registro delle vecchie glorie, e si gestiscono le proprie polisportive: fondazione, password facoltativa, mercato con i filtri, ingaggi, acquisti e offerte, vendite, svincolo, bilancio, stipendi e arretrati, chiusura; e si giocano le amichevoli, da ascoltare dal vivo, con i suoni della pallina, dei colpi e dell'arbitro che si muovono sul tavolo, oppure da leggere alla fine, con la cronaca da salvare su file. Il mondo avanza anche mentre la finestra è aperta, e la barra di stato lo annuncia. Ogni evento della finestra ha il suo effetto sonoro, preso dalla collezione condivisa di GBUtils, e il volume degli effetti e quello della partita si regolano dal menu Impostazioni, da 0, che li spegne, a 100; `ascolta_suoni.py` fa sentire tutti quelli della finestra, gruppo per gruppo, e `strumenti/ascolta_partita.py` quelli della partita. Il file `suoni_di_mess.txt` elenca ogni azione con il suono che la accompagna, per ritoccarli con Acu_Maker. Le partite seguono il regolamento IBSA dello showdown. L'allenamento arriverà con la tappa 11; fino ad allora si fa con l'interfaccia testuale del vecchio `sd.py`, che si avvia con:

    python Showdown.py --testo

Salvataggi e registri stanno accanto al programma, e così le impostazioni d'aspetto, i volumi e la velocità di gioco, nel file `mess_impostazioni.json`. Le cronache salvate delle partite stanno nella cartella `cronache`, un file per incontro. La cartella `strumenti` contiene il banco di prova del motore di partita, con i rapporti di prima e dopo la tappa 9, la taratura del valore, la simulazione lunga dell'economia, gli ascolti e il banco alla cieca della partita sonora, lo script dell'elenco dei suoni e quello che scrive descrizioni fisiche di prova; la cartella `tests` la suite di pytest.

## Accessibilità

MESS è pensato per essere usato con uno screen reader e con il display braille. La nuova interfaccia userà testi discorsivi, senza separatori grafici né tabelle allineate a colonne.

## Installazione da sorgente

Serve Python 3.14. Il programma usa GBUtils, la libreria condivisa del parco software di IZ4APU, che non sta su PyPI e va clonata a parte:

    git clone https://github.com/GabrieleBattaglia/GBUtils.git

poi si mette la sua cartella in PYTHONPATH.

## Dati

La cartella `dati` contiene le collezioni di nomi e cognomi, un file di testo per collezione e una voce per riga, che si possono correggere o ampliare con un qualsiasi editor, e il vocabolario delle descrizioni fisiche, `vocabolario.json`, con cui il gioco compone l'aspetto di ogni giocatore.

Il mondo si salva accanto al programma nel file compresso `mess_mondo.json.gz`, con la copia di sicurezza `mess_mondo.json.gz.bak`, e a finestra aperta si salva da solo a ogni avanzamento e a ogni operazione sulle polisportive. Il file è firmato: una modifica fatta a mano viene scoperta, e il gioco riprende dalla copia. I file che non si possono leggere finiscono nella cartella `salvataggi_illeggibili`. Le uscite di scena dei giocatori restano nel registro delle vecchie glorie, dentro il salvataggio, e si annotano anche in `vecchie_glorie.log`, e le cronache delle partite, quando si chiede di salvarle, in `log_partite_showdown.txt`.

## Autori

Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
