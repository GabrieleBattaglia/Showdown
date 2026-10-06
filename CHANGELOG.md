# Changelog - MESS, Manageriale e Simulatore Showdown

Tutti i cambiamenti e le novità introdotte nelle versioni di MESS.
Il changelog nasce con la versione 1.0.0, il 2 ottobre 2026. Il vecchio sd.py, arrivato alla versione 25.4.24, conta come serie 1: durante i lavori del piano di sviluppo la versione avanza come 1.y.z, e la nuova interfaccia a finestra uscirà come 2.0.0. Ogni versione ha la sua voce, scritta insieme alle modifiche.

## [1.30.1] - 2026-10-06

### Le polisportive nella finestra, e il mercato

Il menu Polisportive ha ora tutte le operazioni. Con Ctrl+N si fonda una polisportiva: il nome resta come lo scrivi, senza maiuscole imposte, e la password è facoltativa, per chi condivide il gioco sullo stesso computer. Con Ctrl+Maiusc+C si sceglie la polisportiva attiva fra le proprie, con la password se è protetta. Dallo stesso menu si mette, si cambia o si toglie la password, e si chiude per sempre una polisportiva, dopo una domanda di conferma.

Il tesseramento si fa al mercato, con Ctrl+K, come in Hattrick. Si aggiungono i filtri che servono, gli stessi della ricerca, si sceglie la probabilità minima che il giocatore accetti e l'ordine dell'elenco, e per ogni giocatore libero si leggono età, valore, gloria richiesta, probabilità di accettare e tratti speciali. A chi interessa si fa un'offerta: costa una delle cinque mosse di mercato del giorno, quindi il gioco chiede conferma, e l'esito arriva in un messaggio. Il giocatore accetta o rifiuta secondo la gloria che chiede, cioè forza, età e caratteristiche rare, e la gloria della polisportiva. Alla chiusura del mercato la vista principale riassume le offerte fatte.

Con Ctrl+Maiusc+S si svincola un tesserato, che torna libero. Le operazioni sulle polisportive si salvano subito.

La ricerca dei giocatori ha nuovi criteri: il sesso, la gloria richiesta e i tratti speciali, cioè mancino, ambidestro, gioco rapido e cambio di velocità.

Le polisportive del computer seguono regole nuove. Scelgono per prime quelle con più gloria, provano ogni candidato una volta sola al giorno, e quando hanno la rosa piena ogni tanto provano a tesserare un libero più forte del tesserato che vale meno: se accetta, prende il suo posto. Prima, appena piene, espellevano il più debole e il giorno dopo ritesseravano, senza motivo; e se un candidato rifiutava, ci riprovavano fino a esaurire le mosse.

Chi si ritira o muore lascia libero il suo posto: prima occupava per sempre uno dei quindici. Le polisportive del computer ritrovano i loro tesserati, che prima portavano scritto un nome diverso da quello della polisportiva: così ora si allenano da soli, e le polisportive del computer che vanno male possono chiudere. Gli ipovedenti chiedono il 10 per cento di gloria in meno, a tutti: prima lo sconto valeva solo per scegliere chi provare, ma non per decidere se accettava.

Il mondo si salva compresso, nel file mess_mondo.json.gz: un mondo di ottomila giocatori pesa 4,5 MB invece di 36. Il vecchio mess_mondo.json si legge ancora, e il primo salvataggio lo sostituisce. Nei mondi grandi un giorno simulato si elabora quasi cinque volte più in fretta.

## [1.22.2] - 2026-10-06

### Il mondo vive anche a finestra aperta, e ognuno ha il suo diario

Il tempo del mondo scorre anche mentre la finestra è aperta. Ogni minuto il gioco controlla se sono passate le 8 ore reali di un giorno simulato: in quel caso fa avanzare il mondo, lo salva e lo annuncia nella quarta riga della barra di stato, per esempio "mondo avanzato di un giorno", senza cambiare il testo che stai leggendo. Il riepilogo completo resta nel menu Mondo, con Ctrl+Maiusc+A. Mentre è aperto un dialogo, il mondo aspetta che si chiuda.

Il tempo non va più perso. Prima, a ogni avvio, il resto inferiore alle 8 ore spariva, e aprendo il gioco ogni 12 ore se ne perdevano 4 ogni volta: ora resta per la volta dopo. Il tempo si misura in UTC, e il cambio dell'ora legale non fa più guadagnare o perdere un'ora al mondo.

Quando passano più giorni insieme, ciascuno ha la sua giornata completa: invecchiamento, guarigioni, ritiri, autoallenamento, mosse delle polisportive del computer e nascite. Prima i giorni contavano tutti per l'età, ma le polisportive del computer e l'autoallenamento avanzavano di un giorno solo. Le nascite non hanno più il tetto di cinquanta per avvio, che dava meno giocatori nuovi a chi apre il gioco di rado: il mondo cresce secondo natura, finché le morti compensano le nascite.

Ogni giocatore e ogni polisportiva ha il suo diario, con la data simulata e le voci più recenti in cima, sul modello di Terminal Beast: l'entrata nel mondo e la fondazione, i tesseramenti, le espulsioni e gli abbandoni, le partite con il punteggio dei set, gli infortuni e le guarigioni, il ritiro e l'uscita di scena. Gli allenamenti consecutivi della stessa caratteristica si fondono in una voce sola, dal valore di partenza a quello d'arrivo. Il diario di un giocatore si apre dal menu Giocatori con Ctrl+Maiusc+D, quello della polisportiva attiva dal menu Polisportive con Ctrl+Maiusc+M.

Dal menu Impostazioni, alla voce Conservazione dei diari, si sceglie per quanti giorni simulati conservare le voci, separatamente per giocatori e polisportive: zero, il valore di partenza, vuol dire per sempre. Le voci più vecchie si tolgono a ogni salvataggio.

Le vecchie glorie hanno il loro registro nel mondo: chi esce di scena, per morte o perché lascia il mondo dello showdown, resta ricordato con la data, l'età, la polisportiva, le partite e il valore finale, e si legge dal menu Mondo con Ctrl+Maiusc+V. Prima la finestra mostrava soltanto gli usciti della sessione.

La fine sessione racconta anche cosa è successo nel mondo durante la sessione: di quanti giorni è avanzato, quanti giocatori sono nati, si sono ritirati o sono usciti di scena.

Nei mondi con migliaia di giocatori un giorno simulato si elabora circa sette volte più in fretta, con risultati identici.

Un salvataggio della versione precedente si aggiorna da solo al primo caricamento.

## [1.16.0] - 2026-10-06

### MESS ha una finestra

Il gioco si apre ora in una finestra, sul modello di Terminal Beast e di Tornello. Ha due aree di testo: la vista principale, grande e in sola lettura, dove ogni comando mostra il suo risultato al posto del precedente con il cursore all'inizio, e la barra di stato, di quattro righe da quaranta caratteri, pensate per il display braille. Tutti i comandi stanno nei menu, ciascuno con il suo tasto rapido; Tab passa da un'area all'altra, F5 porta sulla vista principale e F7 sulla barra di stato. Le finestre si adattano ai caratteri grandi di Windows.

La barra di stato è scritta a codici, una lettera e un numero, come in meditimer: la data simulata e il tempo che manca al prossimo avanzamento; la polisportiva attiva con gloria, tesserati e mosse di mercato rimaste; i giocatori liberi, tesserati, fermi e in tutto, con il numero delle polisportive; e l'ultima cosa successa. La legenda è nella guida ai comandi, con F1.

La scheda del giocatore segue quelle dei mostri di Terminal Beast: l'intestazione in una riga, la descrizione, i tratti speciali, le caratteristiche due per riga con un aggettivo alla Hattrick, da Inesistente a Divino, e il valore fra parentesi, la carriera e tre classifiche, generale, del proprio sesso e della propria tendenza, con la posizione e la percentuale. Il giocatore si sceglie scrivendone il numero o il nome: l'elenco si restringe mentre si scrive.

C'è anche la scheda della polisportiva attiva, con palmarès e tesserati, e poi l'elenco di tutti i giocatori, la classifica per valore, la TOP 10, le statistiche del mondo, le liste dei nuovi arrivati, dei ritirati e degli usciti di scena della sessione, l'elenco delle polisportive, la data simulata con il prossimo avanzamento e il riepilogo dell'ultimo avanzamento.

La ricerca si fa scegliendo dove cercare, una caratteristica, una condizione e un valore; "minore di" ora vuol dire davvero minore, e non più minore o uguale.

All'apertura il gioco dà il bentornato, dice quanto tempo è passato dall'ultimo avanzamento e racconta a parole cosa è successo nel frattempo: nascite, ritiri, uscite di scena, guarigioni e mosse delle polisportive del computer. Alla chiusura il mondo si salva e una finestra riassume la sessione.

Dal menu Impostazioni si scelgono la dimensione dei caratteri e i colori del testo e dello sfondo, che il gioco ricorda sul computer in uso. Il menu Aiuto ha la guida ai comandi, le novità, le informazioni sul gioco e la voce Offrimi un caffè, l'unico posto in cui compare l'invito.

L'interfaccia testuale di prima resta disponibile avviando il gioco con `python Showdown.py --testo`, per le operazioni che nella finestra non sono ancora arrivate: polisportive, partite e allenamento.

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
