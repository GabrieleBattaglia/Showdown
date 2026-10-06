# Changelog - MESS, Manageriale e Simulatore Showdown

Tutti i cambiamenti e le novità introdotte nelle versioni di MESS.
Il changelog nasce con la versione 1.0.0, il 2 ottobre 2026. Il vecchio sd.py, arrivato alla versione 25.4.24, conta come serie 1: durante i lavori del piano di sviluppo la versione avanza come 1.y.z, e la nuova interfaccia a finestra uscirà come 2.0.0. Ogni versione ha la sua voce, scritta insieme alle modifiche.

## [1.3.0] - 2026-10-06

### Un mondo nuovo, in un salvataggio che si protegge da solo

Il mondo del vecchio programma, che in realtà non era mai partito, lascia il posto a uno nuovo: al primo avvio nascono 50 giocatori, e la data simulata parte da oggi.

Tutto il mondo sta ora in un solo file, `mess_mondo.json`, accanto al programma. È un file di testo leggibile, ma porta una firma: se qualcuno lo modifica a mano con un editor, il gioco se ne accorge e non lo usa. Riformattarlo, invece, non conta: spazi e a capo non toccano la firma.

A ogni salvataggio il file precedente diventa la copia di sicurezza, `mess_mondo.json.bak`. Se il salvataggio si rovina o risulta modificato, il gioco riprende dalla copia da solo, e mette da parte il file scartato nella cartella `salvataggi_illeggibili`. Se non si legge nemmeno la copia, il gioco si ferma senza salvare nulla, così da non coprire i file con un mondo nuovo.

Il salvataggio si scrive prima in un file temporaneo e poi prende il posto del vecchio in un colpo solo: un'interruzione a metà, anche una mancanza di corrente, non lo rovina più.

Il numero di un giocatore non passa più a un altro quando lui esce di scena: il registro delle vecchie glorie non confonde più due persone diverse.

Le password delle polisportive non sono più conservate: il gioco tiene soltanto la loro impronta, da cui la password non si può ricavare.

Con lo stesso seme del caso il gioco genera sempre lo stesso mondo, e le prove del motore si possono ripetere identiche.

## [1.1.3] - 2026-10-06

### Il programma si avvia con Showdown.py, da qualunque cartella

Il vecchio file unico `sd.py` è stato diviso in moduli, uno per ogni parte del gioco: il mondo che scorre, il motore delle partite, l'allenamento, l'archivio e l'interfaccia testuale. Il gioco si comporta esattamente come prima, schermate e salvataggi compresi: lo ha verificato una sessione completa di prova, eseguita sul vecchio e sul nuovo codice con risposte, data e caso identici, che ha prodotto due risultati uguali riga per riga.

Ora il programma si avvia con `python Showdown.py`, e lo si può lanciare da qualunque cartella: salvataggi, registro delle vecchie glorie e cronache delle partite stanno sempre accanto al programma, mentre prima finivano nella cartella da cui lo si avviava.

I salvataggi si rileggono anche quando il gioco non è lanciato direttamente, e il loro lettore accetta soltanto i dati del gioco: un file costruito apposta non può più far eseguire nulla al programma.

## [1.1.0] - 2026-10-02

### Descrizioni fisiche nuove, che invecchiano con il giocatore

Le descrizioni fisiche non sono più frasi fatte incollate una all'altra, ma testi composti con un motore grammaticale: articoli, accordi di genere e numero e preposizioni sono sempre giusti, e cinque modelli di frase diversi evitano che si somiglino tutte. Circa un giocatore su tre ha una particolarità che salta all'occhio, come lo sguardo bicolore, un tatuaggio, una voce che si riconosce fra mille o le perline fra le trecce, e ogni tanto il colore degli occhi o dei capelli arriva con una similitudine.

La descrizione non è più scritta una volta per tutte: si compone ogni volta che si apre la scheda, con l'età del momento. Con gli anni i capelli si fanno brizzolati e poi bianchi, compaiono le rughe, a qualcuno cadono i capelli, e chi era un ragazzino diventa un uomo o una donna, con la barba o il trucco.

Anche altezza e peso seguono l'età e il sesso: un ragazzino di nove anni cresce fino ai diciotto, e da adulto il suo peso cambia con gli anni come accade alle persone vere.

I giocatori nati con le versioni precedenti conservano la descrizione che avevano.

## [1.0.0] - 2026-10-02

### MESS diventa un progetto autonomo

Showdown ha lasciato la raccolta Stuff ed è diventato un repository a sé, con un piano di sviluppo a tappe che porterà alla versione 2.0.0.

Le collezioni di nomi, cognomi e frasi descrittive non sono più archivi binari ma file di testo nella cartella `dati`, una voce per riga, che si possono correggere con un qualsiasi editor. I nomi e i cognomi sono allineati con quelli del programma CLZ.

La versione passa dal formato data, 25.4.24, al formato x.y.z del parco software, e il programma la mostra all'avvio. I giocatori e le polisportive creati da qui in avanti portano scritta la versione 1.0.0.
