# Changelog - MESS, Manageriale e Simulatore Showdown

Tutti i cambiamenti e le novità introdotte nelle versioni di MESS.
Il changelog nasce con la versione 1.0.0, il 2 ottobre 2026. Il vecchio sd.py, arrivato alla versione 25.4.24, conta come serie 1: durante i lavori del piano di sviluppo la versione avanza come 1.y.z, e la nuova interfaccia a finestra uscirà come 2.0.0. Ogni versione ha la sua voce, scritta insieme alle modifiche.

## [2.0.0] - 2026-10-23

Il primo rilascio di MESS, compilato per Windows a 64 bit e con l'installatore. Con la 2.0.0 il rifacimento del vecchio sd.py è compiuto: le quattordici tappe del piano di sviluppo sono fatte.

### Installare e aggiornare

MESS si installa con MESS-Setup, che chiede di accettare la licenza GPL 3 e mette il programma nella tua cartella dei programmi, senza permessi di amministratore; oppure si scompatta lo zip in una cartella dove puoi scrivere, mai in Programmi, perché di serie il mondo si salva nella cartella Mondo accanto al programma. Windows può mostrare l'avviso di SmartScreen, perché il programma non è firmato: Altre informazioni, poi Esegui comunque.

All'avvio MESS controlla se su GitHub c'è una versione nuova e propone di installarla, con le sue note: con Aggiorna la scarica, salva il mondo, si chiude e si riapre aggiornato; con Non adesso, o se non rispondi entro due minuti, te la ripropone alla prossima apertura. Ogni esito ha il suo suono.

Si apre una copia sola di MESS: lanciarlo una seconda volta riporta in primo piano quella già aperta. Un errore imprevisto si annota nel file MESS - Errori.log, accanto al programma, e un crash nel file MESS - Crash precedente.log, che la vista segnala all'apertura dopo: sono i file da allegare quando chiedi aiuto.

### L'aiuto

Il manuale si apre nel browser con Maiusc+F1, dal menu Aiuto, con un titolo per ogni argomento. Nello stesso menu ci sono Entra al PUB, che prepara la mail per iscriversi alla lista di supporto degli utenti, e Chiedi aiuto al PUB, che prepara la mail con la tua domanda e le informazioni sul computer. MESS non spedisce mai niente da solo; senza un programma di posta ti guida a copiare i campi uno per volta. F3, Informazioni, dice anche la licenza.

### Il mondo è l'Italia

Il mondiale è diventato il Campionato italiano maschile e femminile, e chi lo vince è campione o campionessa d'Italia; la classifica mondiale è la Classifica nazionale, Ctrl+Maiusc+W, e le statistiche del mondo sono le Statistiche nazionali, Ctrl+I.

Ogni polisportiva ha la sua sede in un comune italiano: quelle del computer la ricevono estratta coi pesi della popolazione, come i giocatori e gli allenatori; quando fondi la tua la scegli tu, da un campo che filtra i comuni mentre scrivi, ciascuno con la percentuale della sua popolazione rispetto a Roma, che vale 100%. La scheda della polisportiva dice la sede.

Il mondo come salvataggio resta il mondo: Salva il mondo, il menu Mondo.

### La cartella del mondo

Tutto quello che riguarda il tuo mondo sta in una cartella sola: il mondo e la sua copia di sicurezza, le impostazioni, i modelli e le formule dei tornei, le cronache e le vecchie glorie. Di serie è la cartella Mondo accanto al programma; con Cartella del mondo, nel menu Impostazioni, ne scegli un'altra con la finestra di Windows, per esempio in Dropbox o su una penna, e porti il mondo fra i tuoi computer. MESS ci sposta i dati, tutti o nessuno; se la cartella scelta ha già un mondo ti chiede quale tenere, dicendoti il più recente, e l'altro va in una sua sottocartella di riserva con la data.

Se all'apertura la cartella scelta non c'è, per esempio perché la penna è staccata, MESS lo dice e propone Riprova, Scegli un'altra cartella ed Esci: un mondo nuovo non nasce mai altrove senza che tu lo sappia. Alla prima apertura di questa versione i dati che le versioni di prova scrivevano accanto al programma passano da soli nella cartella Mondo. Accanto al programma restano soltanto i registri degli errori e, se la cartella del mondo non è quella di serie, il file mess_cartella_del_mondo.json che ricorda dove sta.

### Le finestre e le parole

Tutte le finestre interne si aprono massimizzate, più comode da leggere con lo screen reader e il display braille, ed Esc chiude dove c'è il pulsante Chiudi. Davanti ai nomi dei tornei c'è l'articolo giusto: convocato al Campionato italiano, iscritta all'Open femminile del giovedì, la coppa d'oro alla Coppa delle polisportive. Nell'invito al caffè Invio nel testo chiude, e un Invio tenuto giù dalla voce del menu non lo chiude appena aperto. Trentanove suoni nuovi, nella collezione di GBUtils dalla V220 alla V231.

### Cosa se ne va

L'interfaccia testuale del vecchio sd.py, python Showdown.py --testo, non c'è più: tutto quello che faceva, e molto di più, sta nella finestra.

### Il salvataggio

Il mondo passa al formato 9: all'aggiornamento ogni polisportiva riceve una sede estratta. Chi arriva da una versione di prova trova i nomi nuovi dei tornei con Ripristina il calendario predefinito, nel menu Tornei, o ripartendo da un mondo nuovo.

### Dal collaudo di gioco

Il riepilogo della sala allenamento e il diario dicono ogni spesa per intero: tutte le caratteristiche che ha fatto salire, ciascuna da un valore all'altro con due decimali, come chiusura sinistra da 14,62 a 14,71, al posto del vago "2 altre caratteristiche di meno". Quando una caratteristica sale così poco che a due decimali sembrerebbe ferma, ha i decimali che servono a vederla salire, come precisione da 0,183 a 0,184.

Nel mercato dei giocatori ogni candidato dice, subito dopo nome e cognome, la classe e l'età completa in anni, mesi e giorni separati dai due punti, come Anna Neri, I1, 17:4:3: è l'età esatta della scheda, contata sul calendario dell'età, dove un anno ha 12 mesi da 9 giorni. Il resto della riga non cambia.

Quando la polisportiva attiva ha finito le mosse di mercato del giorno, la voce Mercato del menu Polisportive non è disponibile, e NVDA la legge così; Ctrl+K non resta muto, ma dice che per oggi le mosse sono finite, col loro suono. La voce torna disponibile col giorno nuovo o cambiando polisportiva attiva.

Nel menu Partite, subito dopo Amichevole, Gioca tutte le amichevoli di, col nome della polisportiva attiva, e Gioca tutte le amichevoli di tutte le tue polisportive fanno giocare in un colpo ogni tesserato che oggi può giocare, contro un avversario scelto a caso fra chi oggi può giocare, con la classe entro 15 livelli dalla sua, in su o in giù, e fuori dalla sua polisportiva, al meglio dei set dell'ultima amichevole, senza la partita dal vivo. Ognuno resta a un incontro al giorno, il mondo si salva, e la vista riassume ogni incontro in una riga, col risultato e i punti allenamento, e in fondo i totali.

Ogni evento ha davvero il suo suono, come promette il manuale: hanno il loro anche il modello di torneo e il file delle formule che non si scrivono, il rilancio a chi ha già rifiutato oggi la tua sfida e la sfida in arrivo che non vale più, le iscrizioni non ancora aperte, quelle già chiuse e Togli sulla Coppa delle polisportive, l'errore che ferma MESS e Allena tutti con i tesserati tutti infortunati, che prima suonavano come un altro evento; la sede che non corrisponde a nessun comune suona come un campo da correggere, e Vai alla fine a incontro finito porta al risultato senza il suono di un salto che non c'è. Il calendario predefinito che si ferma a metà del ripristino dice in quale cartella sono già finiti i file di prima.

Il valore di una spesa d'allenamento piccola, nel messaggio breve, nell'anteprima e nella domanda di conferma, non sembra più fermo, da 144,4 a 144,4, ma ha i decimali che servono a vederlo salire, come da 144,400 a 144,402; Allena tutti con tutto al massimo parla soltanto di chi ha un punto da spendere, al femminile quando sono tutte donne. Un modello di torneo rinominato cambiando soltanto le maiuscole non sparisce più, come succedeva su Windows, e i ripieghi del calendario dopo il sorteggio suonano come le iscrizioni chiuse.

Il lungolinea che va in porta si sente sul suo lato fino all'angolo, dove gira in silenzio verso la tasca, e passa al centro soltanto all'ultimo, come sul tavolo vero; prima arrivava centrale già dallo schermo (issue 10). La cronaca lo racconta con Un veloce lungolinea si insacca nella porta di, seguito dal nome di chi subisce, e il goal di diagonale con La diagonale prende precisa il punto G e finisce in goal. I risultati delle partite non cambiano.

I blocchi avvengono soltanto sulle sponde: la paletta ferma la pallina contro la sponda, con un suono suo, e il controllo palla la porta al punto da cui parte il tiro, dal blocco stesso, dal centro o dall'altra sponda, secondo il colpo e la qualità del controllo del giocatore; la pallina sfuggita al controllo rotola via e si ferma a centrocampo. La cronaca dice il blocco sulla sponda e, al livello normale, dove il giocatore porta la pallina (issue 11). La scelta del tiro migliore dopo il blocco, che cambia gli esiti, è la issue 13.

Lo schermo centrale dice quello che succede quasi sempre al tavolo: la pallina di Rossi batte sullo schermo e torna indietro, al posto di urta lo schermo e si ferma. Nella partita dal vivo lo schermo si sente come l'hai scelto all'ascolto di confronto, sei punti su sei: la pallina batte sulla tavola di legno, che risuona dalla metà strada verso il centro dello schermo, più forte di prima, poi ricade sul tavolo e torna indietro rotolando verso chi l'ha tirata, abbastanza forte da sentirsi sotto il fischio, e si ferma da sola dopo un tratto fra 120 e 150 centimetri; l'arbitro fischia sempre all'urto, e a qualunque velocità di gioco, anche cambiata a metà punto, la recupera soltanto quando è ferma (issue 12). Gli esiti delle partite non cambiano.

## [1.94.6] - 2026-10-23

Le correzioni del collaudo con NVDA della 1.94.0, fatto da Gabriele il 23 ottobre 2026.

La finestra si apre massimizzata.

All'apertura col mondo appena aggiornato, il fischietto della notizia dello staff arriva un secondo dopo la fine del suono dell'avvio: prima lo seguiva subito e si confondeva con lui.

Nella scheda di un allenatore la fine della carriera si dice con l'anno del calendario simulato, Sarà in attività sperabilmente fino al 2056, al posto di Smetterà di allenare fra circa 30 anni simulati.

L'indole da muro si chiama granitica, e il programma d'allenamento che le corrisponde granitico: un muro di granito, che blocca e difende. Cambia soltanto il nome, i salvataggi restano come sono. Anche l'interfaccia testuale ora accorda il programma, granitico, aggressivo, e non più granitica o aggressiva.

Le percentuali si scrivono col simbolo, in tutta l'app e nella guida ai comandi, perché sono più corte sul display braille: Fedeltà 2%, la classe al 37% verso G3, Accetterebbe al 64%, Qualità dello staff 56%, e le fasce della cronaca tecnica.

Davanti a un numero che si legge con una vocale l'articolo si elide: Accetterebbe all'8%, all'11%, all'80%, oggi l'1,5%, al posto di al 8% e il 1,5%.

## [1.94.0] - 2026-10-22

### Lo staff delle polisportive

Ogni polisportiva può avere uno staff: un capo allenatore e due assistenti. Lo staff fa imparare più in fretta, abbassa il rischio d'infortunio in allenamento e in partita e fa crescere prima la fedeltà al club. Conta la qualità dello staff, che viene per il 70 per cento dal capo, per il 20 dall'assistente migliore e per il 10 dall'altro. Rispetto allo staff medio del mondo di quel giorno, senza staff si impara circa il 15 per cento più piano, col migliore fino al 20 per cento più in fretta, e il rischio d'infortunio cambia del 15 per cento; la fedeltà cresce fino a un quarto più in fretta. Il mondo nel suo insieme si allena come prima: ogni giorno i fattori si dividono per la loro media sui tesserati. I liberi si allenano senza staff.

Gli allenatori sono di due tipi. Gli ex giocatori: chi si ritira con una classe migliore di almeno H0 diventa allenatore, e la sua classe da allenatore è la classe migliore della carriera; il massimo è A1. I nati allenatori: il mondo genera adulti fra i 35 e i 60 anni, circa uno ogni venti nascite, uomini e donne, vedenti per tre quarti, con l'aspetto descritto a parole e una classe a caso da H0 in su, più rara quanto più è alta. Si smette di allenare fra i 65 e i 75 anni, o alla morte; chi diventa allenatore dopo quell'età allena comunque cinque anni.

### Lo staff della polisportiva attiva e il mercato degli allenatori

Nel menu Polisportive, Staff della polisportiva attiva, Ctrl+H, mostra i tre posti, Capo, Assistente 1 e Assistente 2, con l'allenatore, lo stipendio, la scadenza e il rinnovo; in testa la cassa, gli stipendi dello staff, le mosse e la qualità dello staff con i suoi effetti. Assumi, Alt+A, apre il mercato per un posto vuoto; Rinnova, Alt+R, propone il rinnovo come per i tesserati, negli ultimi tre mesi, una proposta al giorno e tre in tutto, con l'esito previsto e il tic della probabilità; Licenzia, Alt+L, chiede conferma con la buonuscita; Scheda e Diario dell'allenatore. Mercato degli allenatori, Ctrl+Maiusc+G, mostra tutti i liberi dal migliore, coi filtri di classe minima, età massima, tipo e sesso, il posto da offrire e l'ingaggio, col tic della probabilità. L'ingaggio porta la reputazione del club, come per i giocatori: un club giovane paga di più i migliori. L'offerta e il licenziamento usano una mossa di mercato. In nessuno dei due dialoghi Invio sugli elenchi fa qualcosa.

Si assumono come i giocatori: un premio d'ingaggio alla firma, uno stipendio fisso fino alla scadenza, il rinnovo e la buonuscita. Lo stipendio cresce in linea retta con la classe, da 20 euro al mese per un capo H0 a 110 per un A1; un assistente chiede la metà. Chi smette o muore nello staff riceve lo stipendio maturato.

Il computer assume il capo e gli assistenti migliori che può pagare con lo sponsor, senza toccare la cassa, che resta ai campioni, e a fine contratto cambia l'allenatore se ne trova uno libero di almeno cinque livelli migliore. Le cifre vengono dalla taratura su otto mondi di sessant'anni: dall'anno 20 il capo c'è in circa il 95 per cento delle polisportive del computer, e i campioni restano liberi un po' più spesso che nella 1.79.0, a ondate, come ha voluto Gabriele: chi ha cassa e gloria li può prendere.

Chi diventa allenatore, perché nasce o si ritira, resta riservato a te per due ore vere, contate dall'avanzamento che lo fa nascere: chi nasce mentre il gioco è chiuso resta tuo per due ore dall'apertura. Quando un tuo tesserato si ritira e può allenare, hai la prelazione per dieci giorni simulati, e la sua fedeltà al club lo fa chiedere meno.

### Le notizie, le schede e le statistiche

Le notizie dell'avanzamento dicono quando un allenatore del tuo staff se ne va per lo stipendio non pagato, torna libero a fine contratto, smette o esce di scena, quando un tuo ritirato può allenare in prelazione e quando un contratto dello staff sta per scadere, ognuna col suo suono; gli allenatori nuovi riservati a te stanno soltanto nel riepilogo, Ctrl+Maiusc+A. La scheda della polisportiva ha lo staff, la sala allenamento dice chi allena, la scheda di ogni giocatore dice la classe migliore della carriera accanto a quella di oggi e, per chi allena, dove. Le statistiche del mondo, Ctrl+I, contano gli allenatori, ex giocatori e nati, liberi e nello staff, per classe, e le polisportive con un capo. La guida ai comandi ha il capitolo dello staff. Ventiquattro suoni nuovi, nella collezione di GBUtils dalla V215 alla V219, con due gruppi in ascolta_suoni.py: Staff, gli allenatori e Staff, le notizie.

### La provenienza

Ogni giocatore e ogni allenatore ha un comune di provenienza, che la scheda dice nella seconda riga: comune, provincia e regione. Il comune si estrae coi pesi della popolazione dalla collezione dei comuni italiani preparata da Gabriele, 1.291 comuni di 110 province e 20 regioni: più un comune è popoloso, più è probabile venire di lì. Nel gioco non pesa su niente; servirà ai tornei provinciali, regionali e nazionali.

### L'aggiornamento del mondo

Il salvataggio passa al formato 8. All'aggiornamento ogni ritirato vivo che può allenare diventa allenatore libero, il mondo riceve gli allenatori nati che avrebbe avuto, tutte le polisportive partono senza staff, tutti i giocatori ricevono un comune, e la vista e il diario delle tue polisportive dicono che il mercato degli allenatori è aperto, col suo suono.

## [1.79.0] - 2026-10-21

### Gli annunci della cronaca

Nella partita dal vivo e nell'ascolto in differita la cronaca si legge da sola: ogni riga nuova, appena l'azione la fa sentire, arriva alla sintesi, al display braille o a tutti e due, senza toglierti il fuoco dal pulsante. Si sceglie dal menu Impostazioni, Annunci della cronaca: Leggi la cronaca in automatico, Alt+L, acceso all'inizio; Dove vanno le righe, Alt+D, alla sintesi e al braille, solo alla sintesi o solo al braille; la Sintesi, Alt+I, automatica, cioè il primo screen reader attivo o la voce di Windows, oppure NVDA, JAWS o la voce di Windows, SAPI5; le Celle del display braille, Alt+C, 40 all'inizio, 0 se non importa; e il Tempo minimo di lettura di ogni blocco in braille, Alt+T, 2.000 millesimi all'inizio. Alla sintesi le righe si leggono una dopo l'altra. Al display ogni riga si divide in blocchi grandi quanto le celle, spezzati fra le parole, e ogni blocco resta almeno per il tempo minimo; il braille arriva da NVDA o da JAWS, anche quando la sintesi è la voce di Windows. Spenta la lettura automatica, la cronaca resta da leggere nel suo campo, con Tab. Il dialogo ha due suoni nuovi, all'apertura e al salvataggio.

La voce e il display vengono da GBsintesi, un modulo nuovo di GBUtils, V214, nato dalla sintesi dei sottotitoli di MeTeOra: per usarlo da sorgente servono accessible_output2 e pywin32.

## [1.78.13] - 2026-10-21

Nella partita dal vivo e nell'ascolto in differita la cronaca cresce riga per riga mentre l'azione suona, e non più soltanto a fine punto o in pausa: anche con Ascolta fino a fine set, con Tab trovi nel campo quello che hai appena sentito. Le righe nuove arrivano in fondo senza spostarti il cursore, il fuoco resta sul pulsante, e NVDA non le legge da solo, così non copre i suoni.

## [1.78.12] - 2026-10-21

### Il mondo che gioca

Il mondo adesso gioca da solo. Ogni giorno simulato si aprono le iscrizioni ai tornei, si sorteggiano le edizioni che cominciano, si giocano le loro giornate e si chiudono quelle finite, con medaglie, premi, esperienza e fedeltà. Tesserati e liberi giocano un torneo ogni due mesi simulati circa; nel giorno di un torneo non si gioca altro, e un torneo si chiude in due o tre giorni, fino a quattro incontri al giorno negli Open e tre nei Gran Premi e ai mondiali. Le partite dei tuoi tesserati si giocano col motore vero, e si possono riascoltare; tutte le altre con un esito rapido, tarato sul motore, che dà le stesse vittorie e le stesse lunghezze dei set. I tornei sono aperti a tutte le classi, separati per sesso, più gli Open misti; quando gli iscritti sono tanti, un'edizione si divide in sedi parallele della stessa forza. Le teste di serie vengono dalla classe, e i compagni di club non finiscono nello stesso girone quando si può. Gli spareggi dei gironi seguono il regolamento eventi della FISPIC. Il calendario predefinito ha dieci modelli: due mondiali, la Coppa delle polisportive, due Gran Premi, quattro Open settimanali e l'Open misto del mese.

### Il calendario e le iscrizioni

Dal menu Tornei, Calendario e iscrizioni, Ctrl+U: con Alt+M scegli che cosa mostrare, le edizioni aperte, quelle dei prossimi 30 giorni o quelle in corso; Alt+E porta alle edizioni, Alt+I ai tuoi tesserati iscrivibili, Alt+C agli iscritti. Iscrivi, Alt+V, paga subito la quota di 10 euro; Togli, Alt+T, la rimborsa. Invio sugli elenchi non fa niente, così non si iscrive nessuno per sbaglio. Iscrizioni dei tuoi atleti, Ctrl+J, apre lo stesso dialogo col fuoco già sui tuoi tesserati. Nella sala allenamento ogni tesserato ha l'iscrizione automatica, Alt+U, accesa all'inizio, che lo manda a un torneo ogni due mesi; a mano puoi iscriverlo quanto vuoi. I liberi giocano gratis.

### Il pannello dei tornei e la differita

Tornei in corso, Ctrl+Y, apre il pannello dei tornei: scegli con Alt+S che cosa mostrare, poi il torneo, Alt+T, la parte, Alt+P, cioè classifica generale, i tuoi incontri, i gironi e il tabellone, la classifica, Alt+C, e gli incontri, Alt+I. Gli incontri dei tuoi si ascoltano in differita, Alt+A, nella finestra dal vivo, o si leggono come cronaca, Alt+L. Finché non li hai sentiti, il risultato resta nascosto; Mostra il risultato, Alt+M, lo svela per un incontro, e Mostra tutti i risultati, Alt+U, per tutti, dopo una conferma.

### Albo d'oro, classifica mondiale e mondiali

Ctrl+Maiusc+B apre l'albo d'oro, che tiene tutte le edizioni per sempre; Ctrl+Maiusc+W la classifica mondiale, anche lei per sempre. Ogni anno solare simulato c'è un mondiale per sesso, con 32 qualificati per i punti guadagnati nell'ultimo anno, al meglio dei 5 dai quarti: vale quattro volte un torneo normale in punti, esperienza, gloria e premi.

### Gli editor dei tornei

Ctrl+Maiusc+J apre l'editor dei modelli di torneo e Ctrl+Maiusc+Y quello delle formule, presi da Terminal Beast e corretti: cambiano le edizioni future del calendario del mondo, e Ripristina il calendario predefinito, nel menu Tornei, torna a quello di partenza.

### Le sfide fra polisportive e la Coppa delle polisportive

Ogni polisportiva può lanciare due sfide al mese, fino a quattro accumulate. Si giocano con la gara a squadre IBSA, set unico a 31, con tre titolari e fino a tre riserve, che imparano un poco anche senza giocare. Dal menu Partite, Ctrl+W lancia una sfida, Ctrl+Maiusc+F mostra quelle in arrivo, a cui si risponde entro il giorno, Ctrl+Maiusc+H lo storico, con le ultime dieci da riascoltare. La formazione la propone il programma e la cambi tu. Chi vince prende una coppa d'oro, chi perde una d'argento, che nella gloria conta poco. Ogni anno le 64 polisportive con più gloria giocano la Coppa delle polisportive. La seconda riga della barra di stato dice, con la d, quante sfide ti restano da lanciare.

### Punti, esperienza, gloria ed economia

I tornei sono ora la prima fonte dei punti allenamento: un incontro di torneo vale molte amichevoli, e un'amichevole vale meno di prima. L'esperienza cresce, dalla fonte più piccola alla più grande, con l'età, le amichevoli, le sfide, il club e i tornei, dove tutti imparano dagli incontri giocati, un poco di più da ogni fase superata, e i primi dodici hanno un premio di piazzamento. La carriera perfetta arriva ancora ad A1 a 50 anni, e la classe ora pesa le caratteristiche come il valore. Nella gloria contano medaglie e coppe degli ultimi cinque anni simulati, per circa metà; la fedeltà cresce con le medaglie vinte insieme al club. I premi dei tornei vengono dalle iscrizioni e da un contributo della federazione; lo sponsor per gloria è più basso. Il computer, quando ha la cassa piena, si permette stipendi più alti per tesserare, comprare e rinnovare: così i campioni del mondo restano tesserati.

### Infortuni, acciacchi, ritiri e fatica

Gli infortuni che fermano sono un quinto di prima; più spesso, a fine incontro, un giocatore si porta dietro un acciacco che per qualche giorno lo fa rendere un poco meno. Chi si fa male durante un incontro si ritira a fine set, e chi non può presentarsi perde a tavolino, 11 a 0 in ogni set. Nei giorni con più incontri, ogni incontro dopo il primo parte con un po' della fatica di quelli prima.

### Il mondo più grande e più veloce

Ogni giorno nascono da 2 a 9 atleti nuovi, e il mondo a regime arriva a circa 20.000 giocatori in attività; le polisportive del computer si contano soltanto sugli attivi, così restano sempre liberi da cercare e tesserare (issue 1). Il giorno simulato, il salvataggio e il caricamento sono più veloci, senza cambiare niente nel gioco.

### Il salvataggio e i suoni

Il mondo si salva nel formato 7: al primo avvio quello vecchio si aggiorna da solo. I suoni nuovi della collezione di GBUtils, dalla V205, accompagnano ogni evento dei tornei, delle sfide e della differita; suoni_di_mess.txt li elenca tutti.

## [1.60.11] - 2026-10-13

Il freno alle battute alte comincia prima: chi allena una battuta sola fino al massimo ora vince circa sei incontri su dieci contro i giocatori della sua forza, come chi allena un colpo solo, invece di tre su quattro. Il freno tocca anche qualche giocatore normale, quasi sempre per meno di mezzo punto su 40.

## [1.60.10] - 2026-10-11

### La sala allenamento

Dal menu Polisportive, Sala allenamento, Ctrl+Maiusc+L, alleni i tuoi tesserati. L'elenco degli allenandi, Alt+L, sta in ordine di nome e dice per ognuno la classe, i punti allenamento da spendere, il programma e l'intensità. Alt+C apre le 24 caratteristiche, ciascuna con l'aggettivo della scala di Hattrick, il numero e il costo del prossimo punto. Puoi spendere a mano: scegli quanti punti in Alt+P, leggi l'anteprima in Alt+N, che si raggiunge anche con Tab, e conferma con Spendi, Alt+S. Oppure Esegui allenamento completo, Alt+E, spende tutti i punti dell'allenando secondo il suo programma, e Allena tutti, Alt+T, fa lo stesso per tutti. Il programma, Alt+G, si sceglie fra le nove indoli, e chi arriva nuovo parte dalla sua; l'intensità, Alt+I, è leggera, normale o intensa. Alla chiusura la vista principale riepiloga le spese e i cambi.

Ogni punto allenamento compra più o meno lo stesso valore qualunque caratteristica tu alleni: la precisione sale piano, le sponde in fretta, e il prezzo sale punto per punto, sempre più vicino al massimo. I ragazzi imparano un po' più in fretta e gli anziani un po' più piano, con la curva di Hattrick, e gli ipovedenti hanno uno sconto del 7 per cento sulle caratteristiche di gioco. Cresce soltanto ciò su cui spendi. I livelli molto alti calano un poco se non si continuano ad allenare, e dai 50 anni resta il declino. Le caratteristiche possono arrivare fino al massimo, a un prezzo altissimo.

### Da dove vengono i punti

Ogni giorno simulato un tesserato riceve un punto di seduta, 0,6 all'intensità leggera e 1,4 all'intensa, e un libero mezzo punto. Un'amichevole dà da 2 a 4,5 punti secondo i set vinti e il risultato, quasi gli stessi al meglio dei 3 e dei 5, e il più debole ne riceve sempre uno in più, anche quando perde. Liberi e giocatori del computer spendono da soli, secondo la loro indole.

### L'intensità e la costanza

L'intensità cambia i punti della seduta e il rischio d'infortunio in partita, e soltanto all'intensa c'è un piccolo rischio d'infortunio in allenamento, che cresce dopo i 30 anni. In partita la stanchezza dipende dalla costanza recente, cioè da quanto il giocatore si è allenato o ha giocato nelle ultime settimane: l'intensa fa reggere meglio la fatica, la leggera un po' meno.

### I contratti

Ogni tesserato ha un contratto. All'ingaggio il giocatore propone la durata, da 4 a 24 mesi del calendario simulato: brevi i giovani, che migliorano e vogliono ritrattare presto, lunghi gli anziani; gli ambiziosi li accorciano, i modesti li allungano. Un mese simulato dura circa 10 giorni veri. Lo stipendio si fissa alla firma e resta quello fino alla scadenza: chi migliora allenandosi non costa di più finché il contratto dura, e il conto arriva al rinnovo.

Dal menu Polisportive, Contratti e rinnovi, Ctrl+Maiusc+K, proponi i rinnovi negli ultimi tre mesi del contratto: lo stipendio in Alt+S e la durata in Alt+D, con l'esito previsto in Alt+I e un tic che fa sentire la probabilità. Il giocatore accetta secondo l'offerta, la sua fedeltà e la gloria della polisportiva. Una proposta al giorno, tre in tutto: al terzo rifiuto non tratta più, e a scadenza torna libero senza che nessuno incassi niente. Il contratto rinnovato parte alla scadenza del vecchio. La barra di stato avvisa quando un contratto entra negli ultimi tre mesi, all'ultimo mese e alla scadenza.

Svincolare a contratto in corso costa una buonuscita, metà degli stipendi che restano, compreso un rinnovo già concordato. Il valore di mercato scende negli ultimi tre mesi, fino al 40 per cento alla scadenza. Anche il computer rinnova i suoi tesserati, oppure li mette in vendita e li lascia scadere. Gli stipendi non pagati liberano il giocatore anche a contratto in corso. La vecchia regola per cui un tesserato appena allenato poteva andarsene non c'è più.

### La classe

Ogni giocatore ha una classe, da K0, la più bassa, ad A1, la più alta: è il numero del livello scritto con una lettera al posto delle decine, così la A va da A1 ad A9, ogni lettera dalla B alla J ha dieci passi, e la K ha soltanto K0. Pesa per il 70 per cento le caratteristiche e per il 30 l'esperienza, e una carriera perfetta, dai 9 ai 50 anni, arriva ad A1. I nati stanno fra la I e la F, i bravi a metà carriera fra la E e la D. La scheda la mostra con la percentuale verso la classe seguente, e la ricerca ha il criterio Classe, con migliore di e peggiore di.

### L'esperienza

L'esperienza cresce da più fonti, dalla più piccola alla più grande: un poco con l'età, anche da liberi; le amichevoli; lo stare in una polisportiva, con un piccolo aiuto dall'esperienza del gruppo; e, con la tappa 12, i tornei.

### Indoli e tratti

Ogni giocatore nasce con un'indole, aggressiva, difensiva, atletica, da muro, di rimessa, di controllo, da battuta, tecnica o completa, che guida la sua spesa e si legge nella scheda. Nascono tre tratti rari: il talento, che impara più in fretta; l'apprendista rapido, che impara molto in fretta e dimentica un po'; la maturazione precoce o tardiva, che sposta gli anni migliori e l'inizio del declino. E ognuno ha la sua ambizione, da modesto ad ambiziosissimo.

### L'economia

Lo sponsor dipende per metà dalla gloria e per metà dal valore di mercato dei tesserati: chi allena guadagna di più finché i contratti durano. Tutta l'economia è ritarata con l'allenamento acceso, e il computer resta in grado di pagare.

### Il motore di partita

Chi ripete sempre lo stesso colpo diventa prevedibile: dopo i primi attacchi, quando un tipo di colpo, contando insieme i due lati, supera un terzo degli attacchi dell'incontro, il difensore ci si abitua e lo para meglio, un poco di più se è esperto. Anche la battuta allenata molto in alto rende sempre meno vicino al massimo: chi spingeva una battuta sola fino al tetto vinceva nove incontri su dieci contro la sua fascia, ora circa tre su quattro, e il gioco dei giocatori normali non cambia. La resistenza allenata conta una volta sola.

### Il salvataggio

Il mondo si salva nel formato 6. Al primo avvio quello vecchio si aggiorna da solo: ogni tesserato riceve un contratto con lo stipendio che ha, e il valore mostrato cambia per tutti con la taratura nuova, mentre caratteristiche e stipendi restano quelli.

### Correzioni

Il computer non tessera più i liberi infortunati finché non guariscono; tu invece li puoi tesserare subito. Lo svincolo nell'interfaccia testuale dice Le o Gli secondo il giocatore. Il valore dei ritirati non si ricalcola più ogni giorno, e il giorno simulato costa meno.

## [1.50.0] - 2026-10-08

### La partita dal vivo

Un'amichevole ora si può ascoltare. Nel dialogo delle opzioni, dopo Ctrl+O, i modi di seguirla sono due: Assisti e Vai alla fine. Vai alla fine mostra nella vista principale il risultato e i punti allenamento, e sotto la cronaca intera. Assisti apre la finestra dal vivo, e la partita si sente dal punto di vista del tuo giocatore: la pallina che corre, rimbalza sulle sponde e passa sotto lo schermo, a destra o a sinistra, vicina o lontana, più cupa quanto più si allontana; i colpi, le parate, il goal che cade nella tasca, i falli, il fischietto dell'arbitro.

Nella finestra dal vivo il pulsante Prosegui ha il fuoco: Invio o spazio fanno sentire il gioco fino al punto seguente, a un fallo o alla fine del set, e mentre suona lo stesso pulsante mette in pausa e riprende. Alt+F ascolta fino alla fine del set. Alt+L cambia il lato d'ascolto e ti porta dalla parte dell'avversario. Alt+V va alla fine e mostra il risultato. Esc esce senza svelare chi ha vinto: l'incontro resta registrato, e il risultato si legge nei diari dei giocatori o nella cronaca salvata. Con Tab arrivi alla cronaca dell'azione appena ascoltata, che lo screen reader non legge da solo, così non copre i suoni. Le pause lunghe, time-out, cambio campo e inizio del set, non si sentono: si leggono nella cronaca.

L'arbitro fischia una volta per i falli, due dopo ogni goal, a lungo alla fine di ogni set, e tre volte alla fine della partita. Dopo il goal c'è una piccola fanfara, e dopo ogni fallo un segnale che lo distingue bene dal goal.

Il punto alla volta con F8 nella vista principale non c'è più: lo sostituisce Assisti. Il menu Partite tiene Amichevole e Salva la cronaca.

### Velocità e volume

Nel menu Impostazioni, alla voce Velocità di gioco, si sceglie quanto durano le pause fra i punti e la procedura dell'arbitro, da 1, il tempo reale, a 8: si parte da 4. L'azione resta sempre a tempo reale. Durante la partita dal vivo i tasti più e meno la cambiano al volo.

Nel dialogo degli effetti sonori, accanto al volume degli effetti, c'è il volume della partita, da 0 a 100, con il suo suono di prova: si parte da 50, e a 100 la partita suona al livello pieno.

### L'elenco dei suoni

Nella cartella del programma c'è suoni_di_mess.txt, con ogni azione della finestra e della partita e il nome del suono che la accompagna nella collezione di GBUtils: serve a ritoccare i suoni con Acu_Maker.

## [1.46.7] - 2026-10-08

L'ascolto guidato dei suoni, ascolta_suoni.py, lasciava una riga vuota dopo l'attesa del via e dopo l'annuncio di ogni gruppo: ora non più.

## [1.46.6] - 2026-10-08

### Le partite, con il regolamento IBSA

Il motore di partita è nuovo, scritto sul regolamento IBSA dello showdown, edizione 2025-2028, con le scelte fatte da Gabriele voce per voce. La battuta deve rimbalzare una volta sola sulla sponda laterale e passare sotto lo schermo, e chi riceve la para come ogni altro colpo. Il goal vale due punti, ogni errore di gioco uno all'avversario, la penalità due. Il set lo vince chi arriva a 11 con due punti di scarto, senza tetto: il vecchio limite dei 17 punti non c'è più. Gli incontri sono al meglio di 3 o di 5 set, con due servizi a testa.

Ogni fallo ha la sua causa e la chiamata dell'arbitro: servizio irregolare, schermo centrale, out, body touch, difesa irregolare, invasione, infrazione paletta, infrazione palla. L'arbitro fa il sorteggio con la moneta, porta la pallina al battitore, annuncia servizio e punteggio, fischia; ci sono il riscaldamento, il cambio campo, i time-out, la palla morta con il servizio ripetuto, le ammonizioni e le penalità, e rarissime palette e palline rotte. Non c'è pubblico. Nel motore c'è anche la gara a squadre, con un set a 31 punti, tre servizi a testa e la rotazione fissa, senza sostituzioni.

Il vecchio motore trasformava in fallo il 94 per cento dei punti, e quasi tutti i goal erano ace di battuta. Ora i goal sono più della metà dei punti, e quattro su cinque nascono dallo scambio; gli scambi durano qualche colpo, a volte più di dieci; il favorito vince più spesso quanto più è forte, e fra due giocatori forti alla pari si vince di poco, e ogni tanto un set va oltre i 12 punti.

### Il giocatore in campo

La stanchezza cresce con i colpi giocati: la frena la resistenza, anche quella allenata, e la accelera l'età, e un giocatore molto resistente regge cinque set. Il colpo si sceglie secondo i propri punti forti e il lato debole dell'avversario, ma riesce bene a chi è lucido e riposato, e leggere l'avversario è da giocatori esperti. Il mancino sorprende con la sua angolazione, e gli avversari, abituati ai destri, sbagliano lato più spesso; l'ambidestro cambia mano per coprire il lato debole.

Ogni giocatore ha un temperamento, da calmissimo a impetuoso, che la scheda dice a parole: l'impetuoso rischia colpi più forti e fa più falli e più ammonizioni, il calmo sbaglia meno; l'esperienza riduce i falli di tutti.

Gli infortuni hanno una sede. Quello al braccio di gioco ferma chiunque, tranne l'ambidestro, che continua con l'altro braccio; chi ha giocato molto di recente rischia di più. L'ambidestro non ha più infortuni cinque volte più rari e cinque volte più brevi.

### Il valore

Il valore complessivo si ricava ora da quanto ogni caratteristica e ogni tratto contano davvero in partita, e non più dalla loro somma alla pari con 33 punti per tratto. Al primo avvio i giocatori cambiano valore uno per uno: chi ha tratti speciali perde qualcosa, chi ha molta precisione o forza sale. Stipendi e gloria richiesta seguono il valore nuovo, ma l'economia nel suo insieme resta quella della versione 1.38.2.

### L'amichevole nella finestra

Nel menu Partite, che si apre con Alt+R, Amichevole, con Ctrl+O, fa giocare un tuo tesserato della polisportiva attiva contro chiunque altro, anche un altro tuo. Nel dialogo delle opzioni scegli al meglio di 3 o di 5 set, come mostrare la cronaca, un punto alla volta, tutta subito o solo il risultato, e il suo livello, sintetica, normale o tecnica; il dialogo ricorda le ultime scelte. L'incontro si gioca e si registra subito. Un punto alla volta, F8 mostra il punto successivo e Ctrl+F8 tutto il resto; Ctrl+Maiusc+O salva la cronaca in un file della cartella cronache, uno per incontro. Ogni giocatore gioca al massimo un'amichevole per giorno simulato, perché ogni amichevole dà punti allenamento. Il menu ha i suoi suoni, quattordici nuovi.

Anche l'interfaccia testuale gioca con il motore nuovo, a 3 o 5 set e con la regola dell'amichevole al giorno. Il salvataggio passa al formato 5, e quello della versione precedente si aggiorna da solo.

## [1.39.6] - 2026-10-07

Al mercato la domanda di conferma di un'offerta, di un acquisto o di un'offerta d'acquisto aveva il Sì già scelto, al contrario di tutte le altre domande della finestra: ora ha il No, così un Invio di troppo non spende una mossa. Per confermare si sceglie Sì.

## [1.39.5] - 2026-10-07

Un giocatore che moriva o lasciava il mondo mentre era in vendita restava nell'elenco delle vendite, e una polisportiva del computer poteva comprarlo: il morto finiva fra i suoi tesserati, e se era tuo incassavi il prezzo. Ora chi esce di scena esce anche dalla vendita, e il computer non compra chi non gioca più, nemmeno da un salvataggio vecchio.

Svincola un tesserato, con le mosse di mercato finite, faceva scegliere il tesserato e solo dopo diceva che le mosse erano finite: ora lo dice subito.

## [1.39.3] - 2026-10-07

### Gli effetti sonori

La finestra ora suona. Ogni evento ha il suo effetto, e nessun suono serve due eventi: l'avvio e l'uscita, i salvataggi, i comandi dei menu, l'apertura di ogni dialogo e il suo esito, gli avvisi che lasciano aperto un dialogo, le notizie del mondo che avanza. Gli esiti diversi della stessa azione si distinguono a orecchio prima di leggere il messaggio: un ingaggio accettato e uno rifiutato, la password giusta e quella sbagliata, un salvataggio riuscito, uno riuscito con un avviso e uno fallito. I suoni vengono dalla collezione condivisa di GBUtils, 39 che c'erano già e 81 fatti apposta per MESS; nessuno è un'onda quadra, salvo quello dell'invito al caffè, come negli altri programmi.

Quando il mondo avanza a finestra aperta suona un solo suono, quello della notizia più importante, insieme alla riga della barra di stato che la dice: è il segnale per premere F7. Vengono prima un salvataggio non riuscito e le notizie delle tue polisportive, cioè tesserati andati via senza stipendio, stipendi non pagati, giocatori venduti, tesserati usciti di scena, ritirati o diventati bandiere; poi il primo del mese, se hai una polisportiva; poi, se il mondo è avanzato di un giorno solo, le morti, le polisportive del computer che chiudono, le uscite premature, i ritiri e le polisportive del computer che nascono. Il giorno qualunque ha il suo suono, un'alba, e le notizie del giorno sono la stessa alba con una coda diversa; un avanzamento di più giorni ha un suono suo. Anche all'avvio, dopo il suono di benvenuto, si sente quello del mondo avanzato mentre il programma era chiuso.

Se il salvataggio automatico dopo un'operazione sulle polisportive non riesce, dopo il suono dell'operazione si sente quello del salvataggio fallito, e la vista principale ne dice il motivo: prima il fallimento passava sotto silenzio.

Nel menu Impostazioni, alla voce Effetti sonori, si sceglie il volume degli effetti, da 0 a 100: a 50 i suoni sono come sono stati pensati, a zero tacciono. Mentre lo si cambia, appena ci si ferma, si sente il suono di prova al volume scelto.

Nel dialogo della cifra d'ingaggio, a ogni ritocco della cifra, un tic breve fa sentire la probabilità che il giocatore accetti, più acuto quanto più è probabile: la nota sotto il campo lo screen reader non la legge quando cambia. Gli elenchi che si restringono mentre si scrive, nella scelta del giocatore e nel mercato, suonano quando restano vuoti e quando tornano ad avere qualcuno. Il campanello di Windows dei pulsanti premuti a vuoto è diventato un suono di MESS, e il pulsante Predefiniti del dialogo Aspetto, su cui lo screen reader non dice niente, ora si sente.

Un errore imprevisto in un comando, che prima finiva soltanto sulla console, ora suona un allarme e lo dice in un messaggio. Pagare gli arretrati con la cassa vuota ora dice che la cassa è vuota, invece di parlare della cifra.

Per ascoltare tutti i suoni con calma, gruppo per gruppo, c'è ascolta_suoni.py, da lanciare dalla cartella del programma: di ogni suono scrive nome e descrizione e aspetta Invio per farlo sentire, spazio lo ripete; le impressioni finiscono in ascolto_suoni.txt, una riga per voce.

## [1.38.2] - 2026-10-07

### L'economia

Ogni polisportiva ha una cassa in euro e parte con 20.000 euro. Il primo di ogni mese simulato, cioè ogni dieci giorni reali circa, incassa lo sponsor, 35 euro per ogni punto di gloria, e paga gli stipendi. Lo stipendio lo decide il giocatore, come in Hattrick: cresce con il valore, con i tratti rari e con l'esperienza, e va da poco più di 100 euro al mese a qualche migliaio per i più forti. Il bilancio della polisportiva attiva si legge con Ctrl+B, e la cassa sta nella seconda riga della barra di stato, alla lettera c, in migliaia di euro.

Al mercato, con Ctrl+K, si sceglie chi mostrare: i liberi, chi è in vendita, i tesserati del computer, o tutti, e si può fissare un costo massimo. A un libero si offre un premio d'ingaggio, una tantum: il giocatore ne chiede uno secondo forza, età e tratti, e la gloria della tua polisportiva glielo fa abbassare o alzare. Scegli tu la cifra, e il gioco ti dice la probabilità che accetti: alla cifra chiesta accetta una volta su due, con un terzo in più quasi sempre. Chi è in vendita si compra al prezzo chiesto. Per un tesserato del computer si fa un'offerta d'acquisto alla sua polisportiva, che lo cede se la cifra arriva al suo valore di mercato, fino a una volta e mezza per il più forte della rosa; quanto basti, però, lo devi indovinare.

Quando la cassa non basta per gli stipendi, nessuno viene pagato e gli stipendi diventano arretrati. Chi li aspetta perde pazienza, e la sua scheda dice l'umore, quanto aspetta e per quanto ancora pazienterà; con Ctrl+Maiusc+P decidi tu a chi dare i soldi che ci sono, e quanti: ricevere soldi rende la pazienza. Quanto dura dipende dalla fedeltà al club, che cresce con i mesi passati insieme: un nuovo arrivato se ne va dopo due mesi senza stipendio, un veterano dopo cinque. Un giocatore su cento è una bandiera: dopo anni nello stesso club gioca anche senza stipendio, e lo scopri solo quando succede. Quando il mondo avanza e i tuoi tesserati restano senza stipendio, la barra di stato lo dice per prima cosa.

Dal menu Polisportive, alla voce Vendite dei tesserati, metti in vendita un tuo tesserato, a un prezzo che parte dal suo valore di mercato, o lo togli dalla vendita: le polisportive del computer lo comprano se il prezzo è giusto e se possono permetterselo.

In una polisportiva cresce l'esperienza di carriera, che per i liberi resta ferma: un giocatore esperto costa di più. I punti esperienza che si spendono in allenamento ora si chiamano punti allenamento.

Le polisportive del computer stanno nei loro conti: tesserano e comprano solo chi possono pagare, e quando non pagano mettono in vendita il loro giocatore più caro.

Nel mercato le voci Ordina per e Fai un'offerta rispondevano tutte e due ad Alt+O: ora Ordina per risponde ad Alt+R.

Un salvataggio della versione precedente si aggiorna da solo: ogni polisportiva riceve il capitale, e fedeltà ed esperienza dei tesserati si ricavano dai mesi passati nel club.

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
