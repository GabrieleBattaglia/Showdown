# MESS, Manageriale e Simulatore Showdown

Un gioco gestionale dello showdown, il tennistavolo per ciechi, pensato da un giocatore cieco. Concepito il 13 aprile 2015 e portato in Python nel 2020.

Il mondo contiene giocatori generati a caso, ciascuno con nome, aspetto fisico descritto a parole e 26 caratteristiche tecniche e fisiche. Tu apri una o più polisportive, tesseri atleti convincendoli con la tua gloria, li alleni e organizzi partite simulate punto per punto. Accanto a te vivono polisportive guidate dal computer, e il mondo scorre con l'orologio vero: ogni 8 ore reali passa un giorno simulato, i giocatori invecchiano, si ritirano e lasciano il posto a nuove leve.

## Stato del progetto

MESS è in fase di rifacimento. Il lavoro segue le tappe del file `piano_di_sviluppo.txt`, che elenca i problemi del vecchio programma, le decisioni prese e l'ordine dei lavori. Il punto d'arrivo è la versione 2.0.0, con un'interfaccia a finestra accessibile.

Fino ad allora il programma è il vecchio `sd.py`, a riga di comando, che si avvia dalla sua cartella con:

    python sd.py

## Accessibilità

MESS è pensato per essere usato con uno screen reader e con il display braille. La nuova interfaccia userà testi discorsivi, senza separatori grafici né tabelle allineate a colonne.

## Installazione da sorgente

Serve Python 3.14. Il programma usa GBUtils, la libreria condivisa del parco software di IZ4APU, che non sta su PyPI e va clonata a parte:

    git clone https://github.com/GabrieleBattaglia/GBUtils.git

poi si mette la sua cartella in PYTHONPATH.

## Dati

La cartella `dati` contiene le collezioni di nomi, cognomi e frasi descrittive, un file di testo per collezione e una voce per riga: si possono correggere o ampliare con un qualsiasi editor.

## Autori

Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
