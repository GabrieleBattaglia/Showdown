export const meta = {
  name: 'mess-tappa12-finale',
  description: 'Tappa 12 di MESS, ultimo giro: accelerazione, decisioni finali di Gabriele, taratura rifatta, verifica e correzione',
  phases: [
    { title: 'Accelerazione', detail: 'giorno e salvataggio, identici al bit' },
    { title: 'Regole', detail: 'le decisioni finali del 14 ottobre' },
    { title: 'Taratura', detail: 'classe, carriera perfetta, economia, prova lunga' },
    { title: 'Verifica', detail: 'correttezza e statistiche' },
    { title: 'Correzione' },
  ],
}

const SCRATCH = args.scratch
const WT = SCRATCH + '\\showdown-tappa12'
const RAMO = 'mondo-che-gioca'
const T12 = SCRATCH + '\\t12'

const CTX = `
CONTESTO COMUNE.
Progetto: MESS, Manageriale e Simulatore Showdown (Python 3.14, wxPython, italiano), gestionale di showdown, lo sport per ciechi, per Gabriele, giocatore cieco che usa NVDA e ama Hattrick. Main è alla 1.60.11 (E:\\git\\mine\\Showdown, da non toccare). La tappa 12, il mondo che gioca, è quasi finita sul ramo ${RAMO}, nel worktree ${WT} (22 commit sopra main, 1.136 prove verdi, ruff pulito, pubblicato): si lavora SOLO lì.
Da leggere prima di tutto: la decisione D32 in piano_di_sviluppo.txt (vincolante); il progetto definitivo ${T12}\\rapporti\\progetto_definitivo.txt; le decisioni finali di Gabriele del 14 ottobre, ${T12}\\decisioni_finali.txt, vincolanti come D32 (i punti da 1 a 11 sono sue risposte, dal 12 al 16 letture tecniche di ClaudIA da applicare); i rapporti delle fasi in ${T12}\\rapporti\\ (in particolare taratura.json, correzione.json, note_correzione.txt e da_decidere.txt); strumenti/taratura_tornei.txt sul ramo.
Regole: commenti in italiano discorsivo; testi per NVDA senza separatori grafici e senza righe vuote; dialoghi accessibili sul modello di quelli esistenti, con controlli nativi a selezione singola; ruff check soltanto (mai ruff format); python -B -m pytest -q (desktop nascosto, nessun suono); mai finestre sul desktop di Gabriele; le prove non toccano i salvataggi veri mess_mondo* né la copia E:\\git\\tmp\\mess-collaudo-t11; GBUtils (E:\\git\\mine\\GBUtils, V205, pubblicata) si tocca SOLO nella collezione Acu_Collection.json, restando V205, con le regole dei suoni (un suono per evento, mai onda quadra, mai doppioni) e commit a parte nel suo main, pubblicato subito con git push origin main; nessun suono sulle casse; gli script di lavoro in una sottocartella tua di ${SCRATCH}, scritti su file e lanciati con python percorso: MAI python -c, MAI python - con un heredoc, mai heredoc per scrivere codice; più processi in parallelo solo con python -B. ATTENZIONE ALLA MEMORIA: si lavora sul GPD Pocket 3, 16 GB, che il 14 ottobre alle 15:46 si è bloccato del tutto mentre un agente profilava il mondo a regime, ed è servito un riavvio forzato. Quindi al massimo DUE processi pesanti insieme (mondi a regime, prova lunga, ricerca dell'economia, banchi grandi), prima di lanciarli controlla la memoria libera (per esempio con Get-CimInstance Win32_OperatingSystem, FreePhysicalMemory) e non partire sotto i 5 GB liberi, misura quanta memoria prende un processo prima di lanciarne un secondo, e non far girare pytest insieme a una simulazione pesante. Se una corsa lunga deve usare quattro semi, falli due alla volta; a fine lavoro nessun python.exe tuo acceso, controllato. Commit con messaggio italiano chiuso da una riga vuota e "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; mai committare i file mess_mondo*; non toccare version.py, CHANGELOG.md, README.md, piano_di_sviluppo.txt e collaudo.txt (la chiusura la fa ClaudIA). Dopo ogni commit importante pubblica SOLO il ramo: git push origin ${RAMO}.
`

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

phase('Accelerazione')
const accelera = await agent(`${CTX}
COMPITO: la decisione finale 4 di Gabriele, ACCELERARE ADESSO il giorno simulato e il salvataggio a regime, senza cambiare gli esiti. Oggi a regime il giorno costa circa 0,7-0,85 secondi in media a processore libero e da 1,4 a 2,1 nel peggiore, contro i bersagli di 0,45 e 0,65; il salvataggio circa 7 secondi. Profila prima, con strumenti/profilo_giorno.py e i mondi di strumenti/mondi_sintetici.py, il giorno medio e il giorno peggiore e il salvataggio; poi accelera le parti più pesanti (mercato e mosse del computer, iscrizioni automatiche, calendario, declino, ricalcoli ripetuti, serializzazione), una per volta. Regola ferrea: ogni accelerazione identica al bit, provata con le impronte di tests/test_identita_motore.py e tests/dati/impronte_tappa_12.json e confrontando il mondo salvato dopo centinaia di giorni con lo stesso seme, tolti gli istanti reali; niente processi paralleli nel mondo, niente che cambi l'ordine delle operazioni in virgola mobile o i tiri del caso. Il salvataggio può cambiare forma solo se il caricamento resta compatibile e una prova lo dimostra. Misura prima e dopo a processore libero, tre volte, e riporta i numeri. ruff, pytest, commit, push del ramo.`, { label: 'accelerazione', phase: 'Accelerazione', schema: LAVORO_SCHEMA })

phase('Regole')
const regole = await agent(`${CTX}
COMPITO: realizza sul ramo le decisioni finali di Gabriele del 14 ottobre che toccano le regole, sopra il lavoro di accelerazione (le impronte vanno aggiornate soltanto dove una regola nuova cambia davvero gli esiti, dicendolo): punto 1, il computer che spende secondo la cassa, cioè uno stipendio massimo e un tetto di prezzo del computer che crescono con la cassa oltre una soglia, con un parametro iniziale da tarare al passo seguente; punto 3, la coppa d'argento delle sfide che nella gloria vale una piccola parte di quella d'oro, con il coefficiente da tarare; punto 7, i pesi della classe uguali ai pesi nuovi del valore, col meccanismo per ricalcolare una volta somma e ancore congelate al passo seguente; punto 8, l'ordine delle fonti d'esperienza età, amichevoli, sfide, club, tornei, con valori di partenza vicini a 2, 2,5, 3, 4,5 e 8; punto 9, la Coppa delle polisportive che dà alla rosa fedeltà come una medaglia ed esperienza di fasi e piazzamenti; punto 10, Invio che negli elenchi di Lancia una sfida e Sfide in arrivo non lancia né accetta più; punto 11, la seconda riga della barra con le sfide da lanciare entro i 40 caratteri; punto 12, la fatica della giornata anche nella gara a squadre e nell'esito rapido a squadre. Prove per ogni punto. ruff, pytest, commit, push del ramo.
Nota: un primo tentativo di questo passo, il 14 ottobre, si è interrotto a metà per il limite dell'account; le sue modifiche a costanti.py e strumenti/carriera_perfetta.py sono nello stash del worktree (git stash list, git stash show -p stash@{0}). Puoi guardarle per idee, ma riparti dal ramo pulito, e lascia lo stash dov'è.
RAPPORTO DELL'ACCELERAZIONE: ${JSON.stringify(accelera)}`, { label: 'regole', phase: 'Regole', schema: LAVORO_SCHEMA })

phase('Taratura')
const taratura = await agent(`${CTX}
COMPITO: rifai la taratura della tappa 12 sul ramo, nell'ordine giusto, sopra accelerazione e regole. 1) I pesi della classe ora uguali al valore: ricalcola una volta con strumenti/carriera_perfetta.py SOMMA_CARRIERA_PERFETTA e ANCORE_CLASSE, che poi tornano costanti congelate. 2) Le fonti dei punti allenamento e dell'esperienza col bersaglio del punto 6 delle decisioni finali: la MEDIA di tutte le carriere perfette arriva ad A1 a 50 anni con 20 di esperienza, con i tornei prima fonte dei punti come vuole D32 e l'ordine dell'esperienza del punto 8. 3) L'economia con strumenti/simulazione_lunga.py: la ricerca della scala e dello sponsor all'anno 10 e della gloria come nel progetto, con la leva nuova del computer che spende secondo la cassa e il coefficiente delle coppe d'argento; poi la prova di 60 anni su quattro semi, con questi bersagli per tutti i 60 anni: cassa mediana del computer fra 2.000 e 15.000 euro, tesserati attorno al 90 per cento e liberi attorno al 9, i primi 100 del mondo per valore tesserati almeno all'80 per cento, la gloria mediana dell'anno 60 entro il 20 per cento dall'anno 20 se si può senza tradire la risposta 11 (il palmarès pesa la metà), gli incontri non regolari a regime attorno a uno su 45 (punto 13); poi lo scenario dell'utente. 4) Il tempo del giorno a regime col lavoro di accelerazione, a processore libero. Aggiorna strumenti/taratura_tornei.txt, discorsivo e senza righe vuote, con i numeri prima e dopo. ruff, pytest, commit, push del ramo. Se un bersaglio non si raggiunge senza cambiare una decisione di Gabriele, fermati su quel punto e mettilo fra le cose da decidere con i numeri.
RAPPORTI: ${JSON.stringify({ accelera, regole })}`, { label: 'taratura', phase: 'Taratura', schema: LAVORO_SCHEMA })

const PROBLEMI_SCHEMA = {
  type: 'object',
  properties: {
    problemi: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, riga: { type: 'integer' }, gravita: { type: 'string', enum: ['alta', 'media', 'bassa'] }, problema: { type: 'string' }, prova: { type: 'string' }, correzione: { type: 'string' } }, required: ['file', 'riga', 'gravita', 'problema', 'prova', 'correzione'] } },
    note: { type: 'string' },
  },
  required: ['problemi', 'note'],
}

const LENTI = [
  { chiave: 'correttezza', testo: `LENTE DELLA CORRETTEZZA E DELLE DECISIONI. Controlla, contro decisioni_finali.txt punto per punto e contro D32, il lavoro di quest'ultimo giro (git log e git diff dei commit nuovi): accelerazioni che cambiano gli esiti o il salvataggio, regole realizzate male o a metà, Invio, barra, coppa, fatica a squadre, pesi della classe e costanti congelate, prove che non provano niente, regressioni. Dimostra ogni difetto con un esempio eseguito.` },
  { chiave: 'statistiche', testo: `LENTE DELLE STATISTICHE. Rilancia con semi nuovi la carriera perfetta e una prova lunga ridotta dell'economia, e il profilo del giorno: la media delle carriere perfette ad A1 a 50 anni; il computer che spende senza andare in rosso né arricchirsi senza fine; i campioni tesserati; gli incontri non regolari; il tempo del giorno.` },
]

phase('Verifica')
const revisioni = await parallel(LENTI.map(l => () => agent(`${CTX}
COMPITO: verifica avversaria, in sola lettura (non modificare file del worktree), di quest'ultimo giro sul ramo ${RAMO}. ${l.testo}
Segnala solo problemi dimostrati, con file, riga, prova e correzione proposta.
RAPPORTI: ${JSON.stringify({ accelera, regole, taratura })}`, { label: `verifica:${l.chiave}`, phase: 'Verifica', schema: PROBLEMI_SCHEMA })))

const problemi = revisioni.flatMap((r, i) => (r ? r.problemi : []).map(p => ({ ...p, lente: LENTI[i].chiave })))
log(`Verifica: ${problemi.length} problemi`)

phase('Correzione')
const correzione = problemi.length === 0 ? null : await agent(`${CTX}
COMPITO: correggi sul ramo i problemi veri segnalati dalla verifica, con una prova per ciascuno dove ha senso, e spiega quelli che respingi. Se i numeri cambiano, rilancia la taratura che serve e aggiorna strumenti/taratura_tornei.txt. ruff, pytest, commit, push del ramo. Nelle note un riassunto breve in prosa per Gabriele dei numeri finali: carriera perfetta, economia a regime, campioni tesserati, infortuni, tempo del giorno e del salvataggio.
PROBLEMI: ${JSON.stringify(problemi)}
RAPPORTI: ${JSON.stringify({ accelera, regole, taratura })}`, { label: 'correzione', phase: 'Correzione', schema: LAVORO_SCHEMA })

return { accelera, regole, taratura, problemi, correzione }
