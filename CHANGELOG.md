# Changelog - MESS, Manageriale e Simulatore Showdown

Tutti i cambiamenti e le novità introdotte nelle versioni di MESS.
Il changelog nasce con la versione 1.0.0, il 2 ottobre 2026. Il vecchio sd.py, arrivato alla versione 25.4.24, conta come serie 1: durante i lavori del piano di sviluppo la versione avanza come 1.y.z, e la nuova interfaccia a finestra uscirà come 2.0.0. Ogni versione ha la sua voce, scritta insieme alle modifiche.

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
