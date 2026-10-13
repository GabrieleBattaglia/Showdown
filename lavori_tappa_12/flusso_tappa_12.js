export const meta = {
  name: 'mess-tappa12',
  description: 'Tappa 12 di MESS, il mondo che gioca: progetto, cuore, finestra, taratura, revisione e correzione secondo D32, su un ramo a parte',
  phases: [
    { title: 'Progetto', detail: 'architetto, critico, architetto finale' },
    { title: 'Decisioni', detail: 'il progetto con le risposte di Gabriele' },
    { title: 'Cuore tornei', detail: 'profilo, issue 1, formule, modelli, motore dei tornei' },
    { title: 'Cuore mondo', detail: 'calendario, esito rapido, sfide, economia, formato 7' },
    { title: 'Finestra', detail: 'menu Tornei, pannello, iscrizioni, editor, sfide, suoni' },
    { title: 'Taratura', detail: 'esito rapido, carriera perfetta, economia, prova lunga' },
    { title: 'Revisione', detail: 'D32, correttezza, statistiche' },
    { title: 'Correzione' },
  ],
}

// args.scratch: lo scratchpad della sessione; args.fase: 'progetto' si ferma dopo l'architetto finale;
// args.decisioni: le risposte di Gabriele alle domande del progetto, se ce ne sono.
const SCRATCH = args.scratch
const WT = SCRATCH + '\\showdown-tappa12'
const RAMO = 'mondo-che-gioca'

const CTX = `
CONTESTO COMUNE.
Progetto: MESS, Manageriale e Simulatore Showdown (E:\\git\\mine\\Showdown, Python 3.14, wxPython, italiano), gestionale di showdown, lo sport per ciechi, per Gabriele, giocatore cieco che usa NVDA e ama Hattrick. Versione 1.60.11, tappe 1-11 fatte. Si lavora alla tappa 12, il mondo che gioca. Leggi in piano_di_sviluppo.txt (di E:\\git\\mine\\Showdown, ramo main) la decisione D32 per intero, VINCOLANTE: sono le scelte di Gabriele del 13 ottobre 2026, comprese le sue regole proprie; poi la tappa 12, il problema P6, D31 per intero (le fonti dei punti e dell'esperienza, la classe congelata, gli agganci), e D6, D9, D12, D13, D18, D19, D20, D22, D23, D24, D25, D26, D27, D29, D30.
Analisi già fatta, da leggere e non rifare: ${SCRATCH}\\t12\\analisi.txt (Terminal Beast e i suoi 20 difetti da non copiare, cosa c'è in MESS, i numeri: costo di un incontro, giorno a regime, volume, diario, infortuni, carriera perfetta, gloria, premi, issue 1, un'architettura proposta) e ${SCRATCH}\\t12\\decisioni_t12.txt (le decisioni gruppo per gruppo, con le letture di ClaudIA). Terminal Beast è in E:\\git\\mine\\Terminal_Beast (cartella viva; Terminal-Beast-Official è vecchia): tournament_engine.py, tournament_manager.py, tournament_gui.py, dialogs/tournament_dialogs.py, convocazioni_gala.py; D9 e D13 dicono di copiarli e adattarli, senza farne utilità di GBUtils, e senza i difetti elencati nell'analisi. Non modificare mai niente in Terminal_Beast.
Regole: commenti in italiano discorsivo; testi per NVDA senza separatori grafici e senza righe vuote; dialoghi accessibili sul modello di quelli esistenti (gui/dialoghi.py: pannello scorrevole, adatta_finestra, etichette con &, avvisa, completa), con controlli nativi a selezione singola, mai Notebook né alberi a selezione multipla; ruff check soltanto (mai ruff format); python -m pytest -q (desktop nascosto, nessun suono: registratore del conftest); mai finestre sul desktop di Gabriele: ogni script che crea finestre wx fuori da pytest passa da sé al desktop nascosto copiando pytest_configure di tests/conftest.py prima di creare wx.App, e gira con un sorvegliante del primo piano; la finestra vera si prova solo da una copia del repo in E:\\git\\tmp con il mondo mess_mondo.json.gz di Gabriele, mai nel worktree né nella cartella viva, e la copia va nel Cestino a fine lavoro; le prove non toccano i salvataggi veri mess_mondo* di E:\\git\\mine\\Showdown né la copia di collaudo E:\\git\\tmp\\mess-collaudo-t11; GBUtils (E:\\git\\mine\\GBUtils, oggi V204) si modifica SOLO nella collezione Acu_Collection.json e nella versione (V205, intestazione e VERSION di GBUtils.py e E:\\git\\mine\\projects.json), con le regole dei suoni (preset nuovi mess_ con descrizione dettagliata, firme "Usato da: mess." sui riusati, mai onda quadra, mai doppioni, un suono per evento) e commit a parte nel repo GBUtils; nessun suono riprodotto sulle casse; gli script di lavoro in una sottocartella tua di ${SCRATCH}, scritti su file e lanciati con python percorso: MAI python -c, MAI python - con un heredoc (due processi così sono rimasti appesi per nove ore), mai heredoc per scrivere codice; più processi in parallelo sugli stessi sorgenti solo con python -B; a fine lavoro nessun python.exe tuo acceso. Si lavora nel worktree ${WT}, ramo ${RAMO} (lo crea il primo agente che scrive codice); commit con messaggio italiano chiuso da una riga vuota e "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; mai committare i file mess_mondo*; non toccare version.py, CHANGELOG.md, README.md, piano_di_sviluppo.txt e collaudo.txt (la chiusura la fa ClaudIA). Chi scrive codice, a fine lavoro e dopo ogni commit importante, pubblica SOLO il ramo con git push -u origin ${RAMO} (mai main, mai il ramo di GBUtils fuori dal suo main): Gabriele vuole tutto salvato, perché il portatile si può spegnere.
`

const PROGETTO_SCHEMA = {
  type: 'object',
  properties: {
    progetto: { type: 'string', description: 'il progetto completo e concreto' },
    domande_per_gabriele: { type: 'array', items: { type: 'string' }, description: 'solo le scelte di gioco che D32 e D31 non fanno o che si leggono in due modi: ciascuna con il problema in breve, le opzioni concrete (2-4) con i loro numeri, e quella che consigli per prima' },
  },
  required: ['progetto', 'domande_per_gabriele'],
}

phase('Progetto')
const bozza = await agent(`${CTX}
COMPITO: sei l'architetto. Scrivi il progetto completo e concreto della tappa 12, che realizzi D32 alla lettera, NON modificando file del repository (puoi lanciare script di misura in sola lettura in una tua cartella dello scratchpad). Deve coprire, con nomi di moduli, classi, funzioni, campi salvati, formule e costanti iniziali:
1. Il profilo del motore e del giorno: perché un incontro in modalità essenziale costa oggi da 4 a 9 millisecondi e non poco più di uno come alla tappa 9, cosa si può accelerare senza cambiare gli esiti, e il bilancio del tempo del giorno simulato col mondo più grande della issue 1 (circa 20.600 attivi).
2. La issue 1 e le nascite da 2 a 9 al giorno.
3. Formule e modelli di torneo, copiati da Terminal Beast e corretti: formule.json e la cartella dei modelli accanto al gioco, i loro campi, la ricorrenza nel modello, la validazione, il calendario predefinito, il ripristino.
4. Il motore dei tornei senza mondo e senza wx (tornei.py o come lo chiami): iscritti per identificativo, teste di serie dalla classe a serpentina con i compagni di club separati, gironi a giornate col metodo del cerchio, classifica di girone senza pareggi con gli spareggi del regolamento IBSA come vuole D6, promozioni, tabellone con le teste di serie che si incontrano il più tardi possibile, turni di riposo, finalina corretta, classifica finale, premi con calculate_prizes copiato, stato tutto salvabile; e le prove, compreso un banco su migliaia di tornei a caso.
5. Il calendario nel mondo: apertura delle edizioni, iscrizioni dei tesserati del computer e dei liberi (gratis), dell'utente a mano e in automatico, sorteggio, giornate giocate fino a tre o quattro incontri al giorno, un impegno al giorno, chiusura con medaglie, premi, esperienza a tutti i partecipanti con fasi superate e piazzamenti a scalare fino almeno al dodicesimo, fedeltà dalle medaglie; il mondiale annuale per sesso con la qualificazione dai punti dell'ultimo anno; la classifica mondiale per sempre; l'albo d'oro; il diario aggregato per torneo.
6. L'esito rapido per le partite senza tesserati dell'utente: come si calcola dalla forza dei due, come si gioca set per set, come si tara sul motore vero con il banco delle partite perché dia le stesse vittorie e le stesse lunghezze dei set, infortuni e ritiro col carico medio; il motore vero per le partite con un tesserato dell'utente, giocate anche a programma chiuso, con risultato, seme e fotografia dei due giocatori salvati per l'ascolto in differita.
7. Il ritiro per infortunio a fine set e la sconfitta a tavolino, 11 a 0 in ogni set, nel motore e nell'esito rapido.
8. Le sfide fra polisportive con la gara a squadre IBSA del motore (set unico a 31, squadre miste da 3 a 6), due al mese accumulabili fino a quattro, l'accettazione come nei galà, la convocazione sul modello di convocazioni_gala.py, la coppa d'oro e d'argento; il torneo a squadre annuale fra polisportive che dà le coppe; la registrazione della gara a squadre nella carriera.
9. L'economia: iscrizione di 10 euro, contributo della federazione che raddoppia il montepremi, voci iscrizioni e premi nei conti e nei bilanci; la gloria col palmarès sugli ultimi 5 anni simulati del calendario; lo sponsor per gloria da ritarare.
10. Le fonti dei punti allenamento e dell'esperienza riequilibrate secondo D32 (tornei prima fonte; l'ordine età, amichevoli, sfide, club, tornei) perché la carriera perfetta resti alla somma congelata e a 20 di esperienza a 50 anni; strumenti/carriera_perfetta.py che gioca davvero il calendario col motore.
11. Il salvataggio al formato 7 con la migrazione dal 6, che non tocca giocatori, contratti né casse.
12. La finestra: menu Tornei (calendario, iscrizioni, tornei in corso con il pannello accessibile senza Notebook, albo d'oro, classifica mondiale, editor dei modelli e delle formule), le sfide nel menu Partite, l'iscrizione automatica nella sala allenamento, l'ascolto in differita nella finestra dal vivo, la scheda con il palmarès, le notizie nella barra (D18), i suoni nuovi uno per evento (D24, V205), la guida.
13. La taratura, nell'ordine giusto (esito rapido sul motore; pesi del valore rimisurati, perché il freno alle battute della 1.60.11 li ha lasciati da rimisurare qui; carriera perfetta e fonti; economia con cerca-economia, la prova di 60 anni sul mondo più grande e lo scenario dell'utente con i tornei), con i bersagli; e le prove automatiche.
14. L'ORDINE DEI LAVORI in quattro passi di realizzazione che si possano affidare a quattro agenti in fila, ciascuno con le prove verdi a ogni commit: Cuore tornei (profilo, issue 1, formule, modelli, motore dei tornei senza mondo), Cuore mondo (calendario, esito rapido, ritiro e tavolino, sfide e gara a squadre, economia, gloria, fedeltà, formato 7, testo minimo nell'interfaccia testuale), Finestra (tutto il punto 12), Taratura (punto 13).
Leggi il codice che serve (mondo.py, partita.py, motore/, economia.py, esperienza.py, allenamento.py, costanti.py, classe.py, contratti.py, modelli.py, archivio.py, testi.py, suoni.py, gui/, cli.py, strumenti/) e i file di Terminal Beast.`, { label: 'architetto', phase: 'Progetto', schema: PROGETTO_SCHEMA })

const CRITICA_SCHEMA = { type: 'object', properties: { obiezioni: { type: 'array', items: { type: 'string' } } }, required: ['obiezioni'] }
const critica = await agent(`${CTX}
COMPITO: sei il critico del progetto qui sotto. Confrontalo con D32 frase per frase, con D31 e con le altre decisioni, e trova ciò che manca, ciò che è diverso dalle scelte di Gabriele, ciò che non regge (tempi del giorno simulato col mondo più grande, esito rapido che non riproduce il motore, carriera perfetta che non torna alla somma congelata, economia che salta coi premi della federazione, gloria, classifiche e spareggi sbagliati, difetti di Terminal Beast copiati, migrazione), ciò che è troppo complicato per chi ascolta il codice con la sintesi vocale, i rischi per l'accessibilità della finestra, e l'ordine dei lavori che non regge con le prove verdi a ogni commit. Verifica i numeri importanti con script di misura in sola lettura nello scratchpad. Non modificare file del repository. Restituisci le obiezioni concrete, ciascuna con la sua gravità.
PROGETTO: ${bozza.progetto}
DOMANDE DELL'ARCHITETTO: ${JSON.stringify(bozza.domande_per_gabriele)}`, { label: 'critico', phase: 'Progetto', schema: CRITICA_SCHEMA })

const progetto = await agent(`${CTX}
COMPITO: sei l'architetto. Rivedi il tuo progetto secondo le obiezioni del critico (accogli quelle giuste, spiega in fondo quelle che respingi) e restituisci il progetto finale completo e autosufficiente, senza rimandi alla bozza. Dove un'obiezione o una tua domanda riguarda una scelta di gioco che D32 e D31 non fanno, scrivi nel progetto la soluzione che consigli e metti la scelta fra le domande per Gabriele, con le opzioni e i numeri che servono a lui per decidere; non chiedere niente che D32 abbia già deciso. Non modificare file del repository.
PROGETTO: ${bozza.progetto}
DOMANDE DELLA BOZZA: ${JSON.stringify(bozza.domande_per_gabriele)}
OBIEZIONI: ${JSON.stringify(critica.obiezioni)}`, { label: 'architetto:finale', phase: 'Progetto', schema: PROGETTO_SCHEMA })

if (args.fase === 'progetto') {
  return { progetto: progetto.progetto, domande: progetto.domande_per_gabriele, obiezioni: critica.obiezioni }
}

phase('Decisioni')
const finale = !args.decisioni ? progetto : await agent(`${CTX}
COMPITO: sei l'architetto. Gabriele ha risposto alle domande del tuo progetto finale: integra le sue risposte, vincolanti come D32, e restituisci il progetto definitivo completo e autosufficiente. Gabriele risponde spesso con regole sue invece che con le opzioni: applicale alla lettera; se una risposta lascia un punto aperto, scegli la lettura più vicina alle sue parole e dillo in fondo. Non modificare file. Lascia vuote le domande, salvo un dubbio vero nato dalle risposte.
PROGETTO FINALE: ${progetto.progetto}
DOMANDE: ${JSON.stringify(progetto.domande_per_gabriele)}
RISPOSTE DI GABRIELE: ${args.decisioni}`, { label: 'architetto:decisioni', phase: 'Decisioni', schema: PROGETTO_SCHEMA })

const LAVORO_SCHEMA = {
  type: 'object',
  properties: {
    commit_showdown: { type: 'array', items: { type: 'string' } },
    commit_gbutils: { type: 'array', items: { type: 'string' } },
    fatto: { type: 'array', items: { type: 'string' } },
    ruff: { type: 'string' },
    pytest: { type: 'string' },
    misure: { type: 'string' },
    da_decidere: { type: 'array', items: { type: 'string' } },
    note: { type: 'string' },
  },
  required: ['commit_showdown', 'commit_gbutils', 'fatto', 'ruff', 'pytest', 'misure', 'da_decidere', 'note'],
}

phase('Cuore tornei')
const cuore1 = await agent(`${CTX}
COMPITO: il primo passo di realizzazione della tappa 12, il CUORE DEI TORNEI, secondo il progetto definitivo qui sotto: il profilo del motore e del giorno con le accelerazioni che non cambiano gli esiti (verificate confrontando il mondo salvato dopo centinaia di giorni con lo stesso seme, tolti gli istanti reali), la issue 1 con le nascite da 2 a 9, formule e modelli di torneo con i file accanto al gioco e il calendario predefinito, il motore dei tornei senza mondo e senza wx, con le sue prove e il banco dei tornei. Niente calendario nel mondo, niente finestra: li fanno i passi seguenti, ma prepara ciò che servirà loro.
PASSO 0: git -C E:/git/mine/Showdown worktree add "${WT}" -b ${RAMO}, e lavora solo lì.
ruff, pytest, commit, push del ramo.
PROGETTO DEFINITIVO: ${finale.progetto}`, { label: 'cuore:tornei', phase: 'Cuore tornei', schema: LAVORO_SCHEMA })

phase('Cuore mondo')
const cuore2 = await agent(`${CTX}
COMPITO: il secondo passo della tappa 12, il CUORE DEL MONDO, sul ramo ${RAMO} nel worktree ${WT}, sopra il cuore dei tornei: il calendario nel mondo con iscrizioni, giornate, un impegno al giorno, chiusure, medaglie, premi, esperienza, fedeltà, mondiale, classifica per sempre, albo d'oro e diario aggregato; l'esito rapido con una prima taratura grezza sul motore; ritiro e tavolino; le sfide con la gara a squadre e il torneo a squadre annuale con le coppe; l'economia con iscrizioni, contributo della federazione, voci dei conti e gloria su 5 anni; le fonti dei punti e dell'esperienza con una prima taratura grezza; il formato 7 con la migrazione; il minimo nell'interfaccia testuale. Niente finestra nuova, ma prepara le funzioni che le serviranno. Prove automatiche per ogni parte; ruff, pytest, commit, push del ramo.
PROGETTO DEFINITIVO: ${finale.progetto}
RAPPORTO DEL CUORE DEI TORNEI: ${JSON.stringify(cuore1)}`, { label: 'cuore:mondo', phase: 'Cuore mondo', schema: LAVORO_SCHEMA })

phase('Finestra')
const finestra = await agent(`${CTX}
COMPITO: il terzo passo della tappa 12, la FINESTRA, sul ramo ${RAMO} nel worktree ${WT}: il menu Tornei con calendario, iscrizioni, tornei in corso e il loro pannello accessibile, albo d'oro, classifica mondiale, editor dei modelli e delle formule copiati da Terminal Beast e corretti; le sfide nel menu Partite; l'iscrizione automatica nella sala allenamento; l'ascolto in differita nella finestra dal vivo; la scheda col palmarès; le notizie nella barra; i suoni nuovi, uno per evento, con la V205 di GBUtils in un commit a parte; suoni_di_mess.txt rigenerato con strumenti/elenco_suoni.py; la guida. Prove in tests/ e la prova della finestra vera da una copia con il mondo di Gabriele su un desktop nascosto, con i suoni registrati, riportando cosa mostra la finestra passo per passo e che la migrazione al formato 7 funziona. ruff, pytest, commit, push del ramo.
PROGETTO DEFINITIVO: ${finale.progetto}
RAPPORTI: ${JSON.stringify({ cuore1, cuore2 })}`, { label: 'finestra', phase: 'Finestra', schema: LAVORO_SCHEMA })

phase('Taratura')
const taratura = await agent(`${CTX}
COMPITO: la TARATURA fine della tappa 12, sul ramo ${RAMO} nel worktree ${WT}, nell'ordine del progetto: l'esito rapido sul motore vero (vittorie per distacco, lunghezze dei set, infortuni, ritiri), i pesi del valore rimisurati con strumenti/taratura_valore.py (il freno alle battute della 1.60.11 li aveva lasciati da rimisurare: allora il peso delle battute scendeva da 0,71 a 0,47; i pesi della classe restano congelati salvo decisione di Gabriele, quindi se cambiano molto riportalo), la carriera perfetta che gioca il calendario vero e arriva ad A1 a 50 anni con 20 di esperienza con le quote di D32, l'economia con la ricerca della scala e dello sponsor all'anno 10, la prova di 60 anni sul mondo più grande della issue 1 con il controllo dei liberi per decennio, lo scenario dell'utente con i tornei, il tempo del giorno simulato. Scrivi un rapporto discorsivo in strumenti/taratura_tornei.txt, senza righe vuote. ruff, pytest, commit, push del ramo.
PROGETTO DEFINITIVO: ${finale.progetto}
RAPPORTI: ${JSON.stringify({ cuore1, cuore2, finestra })}`, { label: 'taratura', phase: 'Taratura', schema: LAVORO_SCHEMA })

const PROBLEMI_SCHEMA = {
  type: 'object',
  properties: {
    problemi: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, riga: { type: 'integer' }, gravita: { type: 'string', enum: ['alta', 'media', 'bassa'] }, problema: { type: 'string' }, prova: { type: 'string' }, correzione: { type: 'string' } }, required: ['file', 'riga', 'gravita', 'problema', 'prova', 'correzione'] } },
    note: { type: 'string' },
  },
  required: ['problemi', 'note'],
}

const LENTI = [
  { chiave: 'd32', testo: `LENTE DI D32, DELLE RISPOSTE DI GABRIELE E DELL'ACCESSIBILITA'. Prendi D32, la tappa 12 e le risposte di Gabriele frase per frase e dimostra dove il lavoro se ne allontana; controlla i dialoghi nuovi con gli occhi di chi usa NVDA (fuoco, etichette, scorciatoie uniche, testi chiari senza righe vuote, informazioni che cambiano raggiungibili e lette, controlli nativi, niente Notebook), il pannello del torneo, l'ascolto in differita, la barra, i suoni nuovi distinti da tutti gli altri.` },
  { chiave: 'correttezza', testo: `LENTE DELLA CORRETTEZZA. Cerca i difetti veri: tornei che non finiscono o finiscono male, classifiche e spareggi sbagliati, un perdente che vince, turni di riposo contati come vittorie, teste di serie mal disposte, giocatori in due impegni nello stesso giorno, iscrizioni pagate due volte o mai, premi che creano o perdono soldi, medaglie e coppe assegnate male, gloria fuori finestra, esperienza o punti dati due volte, tavolino e ritiro incoerenti, sfide che restano appese, migrazione al formato 7 che perde dati o non è deterministica, salvataggi vecchi illeggibili, motore che cambia a parità di seme dove non deve, regressioni, prove che non provano niente. Dimostra ogni difetto con un esempio eseguito.` },
  { chiave: 'statistiche', testo: `LENTE DELLE STATISTICHE. Rilancia con semi nuovi la carriera perfetta, la simulazione lunga dell'economia, il banco del motore e il banco dei tornei: la carriera perfetta arriva ad A1 a 50 anni e non prima, con le quote delle fonti di D32; l'esito rapido riproduce il motore; il computer regge (tesserati, liberi rimasti, casse, stipendi minimi) per 60 anni sul mondo più grande; gloria e premi non esplodono; il giorno simulato sta in tempi accettabili.` },
]

phase('Revisione')
const revisioni = await parallel(LENTI.map(l => () => agent(`${CTX}
COMPITO: revisione avversaria, in sola lettura (non modificare file del worktree), del lavoro sul ramo ${RAMO} nel worktree ${WT}. ${l.testo}
Segnala solo problemi dimostrati, con file, riga, prova e correzione proposta.
PROGETTO DEFINITIVO: ${finale.progetto}
RISPOSTE DI GABRIELE: ${args.decisioni || 'nessuna'}
RAPPORTI: ${JSON.stringify({ cuore1, cuore2, finestra, taratura })}`, { label: `revisione:${l.chiave}`, phase: 'Revisione', schema: PROBLEMI_SCHEMA })))

const problemi = revisioni.flatMap((r, i) => (r ? r.problemi : []).map(p => ({ ...p, lente: LENTI[i].chiave })))
log(`Revisione: ${problemi.length} problemi`)

phase('Correzione')
const correzione = problemi.length === 0 ? null : await agent(`${CTX}
COMPITO: correggi sul ramo ${RAMO} nel worktree ${WT} i problemi veri segnalati dai revisori, con una prova per ciascuno dove ha senso, e spiega quelli che respingi. Se i numeri cambiano, rilancia la taratura che serve e aggiorna strumenti/taratura_tornei.txt; se cambiano i suoni, aggiorna la collezione (sempre V205 se non pubblicata) e suoni_di_mess.txt. ruff, pytest, commit, push del ramo. Nelle note un riassunto in prosa per Gabriele: come si usano il menu Tornei, il pannello, le iscrizioni e le sfide tasto per tasto, come funziona il calendario, e i numeri principali.
PROBLEMI: ${JSON.stringify(problemi)}
RAPPORTI: ${JSON.stringify({ cuore1, cuore2, finestra, taratura })}`, { label: 'correzione', phase: 'Correzione', schema: LAVORO_SCHEMA })

return { domande: finale.domande_per_gabriele || [], progetto: finale.progetto, cuore1, cuore2, finestra, taratura, problemi, correzione }
