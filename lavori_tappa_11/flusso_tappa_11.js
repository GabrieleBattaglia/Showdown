export const meta = {
  name: 'mess-tappa11',
  description: 'Tappa 11 di MESS: progetto, cuore, finestra, taratura, revisione e correzione dell\'allenamento secondo D31, su un ramo a parte',
  phases: [
    { title: 'Progetto', detail: 'architetto, critico, revisione' },
    { title: 'Cuore', detail: 'allenamento, contratti, esperienza, classe, economia' },
    { title: 'Finestra', detail: 'sala allenamento, contratti, scheda, suoni' },
    { title: 'Taratura', detail: 'carriera perfetta ad A1, economia con l allenamento' },
    { title: 'Revisione', detail: 'D31, correttezza, statistiche' },
    { title: 'Correzione' },
  ],
}

const SCRATCH = 'C:\\Users\\Utente\\AppData\\Local\\Temp\\claude\\E--git\\dc4e79db-fff5-47c7-a3b0-cdd305309903\\scratchpad'
const WT = SCRATCH + '\\showdown-allenamento'

const CTX = `
CONTESTO COMUNE.
Progetto: MESS, Manageriale e Simulatore Showdown (E:\\git\\mine\\Showdown, Python 3.14, wxPython, italiano), gestionale di showdown, lo sport per ciechi, per Gabriele, giocatore cieco che usa NVDA e ama Hattrick. Versione 1.50.0, tappe 1-10 fatte. Si lavora alla tappa 11, l'allenamento. Leggi in piano_di_sviluppo.txt (di E:\\git\\mine\\Showdown, ramo main) la decisione D31 per intero (VINCOLANTE: e' il disegno di Gabriele), la tappa 11 (con la classe da A1 a K0, l'esperienza al 30 per cento, le fonti dell'esperienza, il riferimento della carriera perfetta dai 9 ai 50 anni che porta ad A1), il problema P8, le decisioni D2, D17, D20, D22, D23, D24, D25, D26, D27, D29, D30, e la tappa 12.
Analisi gia' fatta (leggila, non rifarla): ${SCRATCH}\\t11\\analisi.json e ${SCRATCH}\\t11\\domande.txt (come funziona oggi l'allenamento con i numeri, i difetti trovati, i modelli di Hattrick con la formula di Schum, il calo DropL, la curva d'eta' 54/(eta+37), i nomi dei livelli di Hattrick in italiano: inesistente, disastroso, tremendo, scarso, debole, insufficiente, accettabile, buono, eccellente, formidabile, straordinario, splendido, magnifico, fuoriclasse, sovrannaturale, titanico, extraterrestre, mitico, magico, utopico, divino).
Regole: commenti in italiano discorsivo; testi per NVDA senza separatori grafici e senza righe vuote; dialoghi accessibili sul modello di quelli esistenti (gui/dialoghi.py: pannello scorrevole, adatta_finestra, etichette con &, avvisa, completa); ruff check soltanto (mai ruff format); python -m pytest -q (desktop nascosto, nessun suono: registratore del conftest); mai finestre sul desktop di Gabriele (prove della finestra vera da una copia su un desktop nascosto, modello ${SCRATCH}\\t9\\prova_finestra_t9.py); le prove non toccano i salvataggi veri mess_mondo*; GBUtils si modifica SOLO nella collezione Acu_Collection.json e nella versione (V204, intestazione e VERSION di GBUtils.py e E:\\git\\mine\\projects.json), con le regole dei suoni (preset nuovi mess_ con descrizione dettagliata, firme "Usato da: mess." sui riusati, mai onda quadra, mai doppioni, un suono per evento) e commit a parte nel repo GBUtils; nessun suono riprodotto sulle casse; gli script di lavoro in una sottocartella tua dello scratchpad, lanciati con python (non python -c ne' heredoc). Si lavora nel worktree ${WT}, ramo allenamento (lo crea il primo agente che scrive codice); commit con messaggio italiano chiuso da "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; niente push; mai committare i file mess_mondo*; non toccare version.py, CHANGELOG.md, README.md e piano_di_sviluppo.txt (la chiusura la fa ClaudIA).
`

const PROGETTO_SCHEMA = {
  type: 'object',
  properties: {
    progetto: { type: 'string', description: 'il progetto completo e concreto' },
    domande_per_gabriele: { type: 'array', items: { type: 'string' }, description: 'solo se qualcosa di D31 si legge in due modi' },
  },
  required: ['progetto', 'domande_per_gabriele'],
}

phase('Progetto')
const bozza = await agent(`${CTX}
COMPITO: sei l'architetto. Scrivi il progetto completo e concreto della tappa 11, che realizzi D31 alla lettera, NON modificando file. Deve coprire, con nomi di moduli, classi, funzioni, campi salvati, formule e costanti iniziali:
1. I punti allenamento: fonti (seduta quotidiana in polisportiva per intensita', meta' per i liberi, amichevoli con quasi gli stessi punti a 3 e a 5 set, premio al piu' debole come oggi, aggancio per tornei e sfide della tappa 12), quando arrivano.
2. La spesa: a mano (quanti punti in quale caratteristica), Esegui allenamento completo e Allena tutti secondo il modello dell'indole; costo tarato sul valore (ogni punto compra piu' o meno lo stesso valore), prezzo che sale punto per punto, curva d'eta' di Hattrick, sconto del 7 per cento agli ipovedenti sulle caratteristiche di gioco, tetti, calo dei livelli alti non allenati alla DropL, declino dopo i 50 come oggi; i tre tratti rari (talento, apprendista rapido che impara e dimentica in fretta, maturazione precoce o tardiva) con le loro frequenze; l'intensita' per giocatore con il suo effetto sugli infortuni attraverso il carico di D26.
3. Le indoli della nascita (archetipi rivisti, correggendo il difetto delle chiavi delle strategie), il modello di spesa che le segue, la scheda che le mostra; e lo stesso modello per liberi e computer.
4. I contratti di D31: durata proposta dal giocatore secondo eta' e ambizione, stipendio fisso fino alla scadenza, rinnovo a trattativa negli ultimi mesi (fedelta', gloria, offerta), libero alla scadenza senza incasso, valore di mercato che scende verso la scadenza, stipendi non pagati che liberano anche a contratto in corso; il contratto nell'ingaggio, negli acquisti, nelle vendite e nelle offerte d'acquisto del mercato (D20-D23); il computer che rinnova o lascia andare; la regola d'abbandono di P8 tolta.
5. L'economia: stipendio invariato nella formula ma fisso nel contratto; sponsor piu' legato al valore della rosa; bersagli: computer che tessera ancora nove giocatori su dieci, casse mediane attorno a 5000 euro, stipendio dei piu' deboli al decimo percentile attorno a 105 euro.
6. L'esperienza dalle sue fonti (eta', amichevoli, polisportiva, tornei e piazzamenti come aganci, esperienza collettiva del gruppo) e la classe: 70 per cento il valore pesato, 30 l'esperienza, soglie fisse da K0 (il minimo di tutto) ad A1 (la carriera perfetta dai 9 ai 50 anni), piu' fitte in basso; il codice e' il numero del livello con la lettera al posto delle decine (A1..A9, B0..J9, K0); la percentuale verso la classe seguente.
7. La stanchezza in partita dalla costanza recente (al posto della resistenza allenata contata due volte nel motore).
8. La scheda con gli aggettivi di Hattrick e i numeri per ogni caratteristica e per l'esperienza, la classe, l'indole, i tratti, il contratto.
9. La finestra: la sala allenamento (scorrere gli allenandi, caratteristiche, portafoglio, spesa a mano, Esegui allenamento completo, Allena tutti, intensita'), i dialoghi del contratto (proposta all'ingaggio, rinnovo), dove sta nei menu, i tasti, i suoni nuovi (uno per evento), la guida.
10. Il salvataggio al formato 6 con la migrazione (contratti per i tesserati di oggi con lo stipendio che hanno, indoli, tratti, esperienza, classe ricavabile), e l'interfaccia testuale (cli.py) adattata al minimo.
11. Il metodo di taratura (la carriera perfetta simulata, la simulazione lunga dell'economia con l'allenamento acceso, i bersagli) e le prove automatiche.
Leggi il codice che serve (modelli.py, allenamento.py, mondo.py, economia.py, mercato.py, partita.py, motore/, valore.py, testi.py, gui/, archivio.py, cli.py, strumenti/simulazione_lunga.py, strumenti/taratura_valore.py).`, { label: 'architetto', phase: 'Progetto', schema: PROGETTO_SCHEMA })

const CRITICA_SCHEMA = { type: 'object', properties: { obiezioni: { type: 'array', items: { type: 'string' } } }, required: ['obiezioni'] }
const critica = await agent(`${CTX}
COMPITO: sei il critico del progetto qui sotto. Confrontalo con D31 frase per frase e con le altre decisioni, e trova cio' che manca, cio' che e' diverso da D31, cio' che non regge (formule che non portano la carriera perfetta ad A1, economia che salta, contratti incoerenti col mercato di D20-D23, stanchezza, migrazione), cio' che e' troppo complicato per chi ascolta il codice con la sintesi vocale, e i rischi. Non modificare file. Restituisci le obiezioni concrete.
PROGETTO: ${bozza.progetto}`, { label: 'critico', phase: 'Progetto', schema: CRITICA_SCHEMA })

const progetto = await agent(`${CTX}
COMPITO: sei l'architetto. Rivedi il tuo progetto secondo le obiezioni del critico (accogli quelle giuste, spiega in fondo quelle che respingi) e restituisci il progetto finale completo. Non modificare file.
PROGETTO: ${bozza.progetto}
OBIEZIONI: ${JSON.stringify(critica.obiezioni)}`, { label: 'architetto:finale', phase: 'Progetto', schema: PROGETTO_SCHEMA })

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

phase('Cuore')
const cuore = await agent(`${CTX}
COMPITO: realizza il CUORE della tappa 11 secondo il progetto finale qui sotto: punti allenamento e loro fonti, spesa e costi, eta', tratti rari, indoli, intensita' e infortuni, calo dei livelli alti, contratti (con mercato, acquisti, vendite, offerte, computer), economia (sponsor col valore della rosa), esperienza e classe, stanchezza dalla costanza recente nel motore, salvataggio al formato 6 con la migrazione, testi della scheda (aggettivi, classe, indole, tratti, contratto), interfaccia testuale minima. NON la finestra nuova (sala allenamento e dialoghi): la fa il passo seguente, ma prepara le funzioni che le serviranno.
PASSO 0: git -C E:/git/mine/Showdown worktree add "${WT}" -b allenamento, e lavora solo li'.
Prove automatiche per ogni parte. Una prima taratura grezza con le simulazioni (la carriera perfetta e la simulazione lunga), quanto basta perche' i numeri siano sensati: la taratura fine la fa un altro agente. ruff, pytest, commit sul ramo.
PROGETTO FINALE: ${progetto.progetto}`, { label: 'cuore', phase: 'Cuore', schema: LAVORO_SCHEMA })

phase('Finestra')
const finestra = await agent(`${CTX}
COMPITO: realizza la FINESTRA della tappa 11 secondo il progetto finale, sul ramo allenamento nel worktree ${WT}, sopra il lavoro del cuore: la sala allenamento (scorrere gli allenandi, caratteristiche, portafoglio dei punti, spesa a mano, Esegui allenamento completo, Allena tutti, intensita'), i dialoghi del contratto (la durata proposta dal giocatore all'ingaggio e all'acquisto, il rinnovo a trattativa), la scheda nella finestra, le voci di menu e la guida, i suoni nuovi (uno per evento, V204 in GBUtils con commit a parte), suoni_di_mess.txt rigenerato con strumenti/elenco_suoni.py. Prove in tests/ e la prova della finestra vera da una copia con il mondo di Gabriele su un desktop nascosto, con i suoni registrati, riportando cosa mostra la finestra passo per passo e che la migrazione al formato 6 funziona. ruff, pytest, commit.
PROGETTO FINALE: ${progetto.progetto}
RAPPORTO DEL CUORE: ${JSON.stringify(cuore)}`, { label: 'finestra', phase: 'Finestra', schema: LAVORO_SCHEMA })

phase('Taratura')
const taratura = await agent(`${CTX}
COMPITO: la taratura fine della tappa 11, sul ramo allenamento nel worktree ${WT}. Bersagli: 1) la carriera perfetta di Gabriele (entra a 9 anni in una polisportiva, buona dotazione naturale, gioca il 90 per cento delle amichevoli possibili, spende tutti i punti, intensita' normale) arriva alla classe A1 a 50 anni, e l'esperienza vicino al massimo; 2) le soglie della classe piu' fitte in basso: i nati fra I e F, i bravi a meta' carriera fra E e D; 3) la simulazione lunga dell'economia con l'allenamento acceso per tutti: il computer tessera ancora circa nove giocatori su dieci, casse mediane attorno a 5000 euro, stipendio dei piu' deboli al decimo percentile attorno a 105 euro, nessuna polisportiva del computer che fallisce in massa; 4) il valore di un punto speso non dipende troppo dalla caratteristica (costo tarato sul valore); 5) la stanchezza dalla costanza recente non cambia i numeri del banco del motore oltre il ragionevole. Usa e aggiorna strumenti/simulazione_lunga.py, strumenti/taratura_valore.py e gli strumenti nuovi che servono (per esempio strumenti/carriera_perfetta.py); scrivi un rapporto discorsivo in strumenti/taratura_allenamento.txt. ruff, pytest, commit.
PROGETTO FINALE: ${progetto.progetto}
RAPPORTI: ${JSON.stringify({ cuore, finestra })}`, { label: 'taratura', phase: 'Taratura', schema: LAVORO_SCHEMA })

const PROBLEMI_SCHEMA = {
  type: 'object',
  properties: {
    problemi: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, riga: { type: 'integer' }, gravita: { type: 'string', enum: ['alta', 'media', 'bassa'] }, problema: { type: 'string' }, prova: { type: 'string' }, correzione: { type: 'string' } }, required: ['file', 'riga', 'gravita', 'problema', 'prova', 'correzione'] } },
    note: { type: 'string' },
  },
  required: ['problemi', 'note'],
}

const LENTI = [
  { chiave: 'd31', testo: `LENTE DI D31 E DELL'ACCESSIBILITA'. Prendi D31 e la tappa 11 frase per frase e dimostra dove il lavoro se ne allontana; controlla la sala allenamento e i dialoghi del contratto con gli occhi di chi usa NVDA (fuoco, etichette, scorciatoie uniche, testi chiari senza righe vuote, la vista aperta dal dato essenziale di D17), la scheda con gli aggettivi e la classe, i suoni nuovi distinti da tutti gli altri.` },
  { chiave: 'correttezza', testo: `LENTE DELLA CORRETTEZZA. Cerca i difetti veri: punti che si creano o si perdono, spesa oltre i tetti o oltre il portafoglio, costi sbagliati, calo che colpisce chi si allena, contratti incoerenti (scadenze, rinnovi, prezzo, acquisti da e verso il computer, giocatori che se ne vanno a contratto in corso senza arretrati), migrazione al formato 6 che perde dati o non e' deterministica, salvataggi vecchi illeggibili, motore che cambia a parita' di seme dove non deve, regressioni, prove che non provano niente. Dimostra ogni difetto con un esempio eseguito.` },
  { chiave: 'statistiche', testo: `LENTE DELLE STATISTICHE. Rilancia con semi nuovi la carriera perfetta, la simulazione lunga dell'economia e il banco del motore: la carriera perfetta arriva davvero ad A1 a 50 anni e non prima; le classi dei nati e dei giocatori a meta' carriera sono dove D31 le vuole; il computer regge (tesserati, casse, stipendi minimi); i liberi crescono poco; i tratti rari si vedono nei numeri senza rompere niente; un punto speso compra piu' o meno lo stesso valore qualunque caratteristica; prestazioni accettabili per la tappa 12.` },
]

phase('Revisione')
const revisioni = await parallel(LENTI.map(l => () => agent(`${CTX}
COMPITO: revisione avversaria, in sola lettura (non modificare file del worktree), del lavoro sul ramo allenamento nel worktree ${WT}. ${l.testo}
Segnala solo problemi dimostrati, con file, riga, prova e correzione proposta.
PROGETTO FINALE: ${progetto.progetto}
RAPPORTI: ${JSON.stringify({ cuore, finestra, taratura })}`, { label: `revisione:${l.chiave}`, phase: 'Revisione', schema: PROBLEMI_SCHEMA })))

const problemi = revisioni.filter(Boolean).flatMap((r, i) => r.problemi.map(p => ({ ...p, lente: LENTI[i] ? LENTI[i].chiave : '' })))
log(`Revisione: ${problemi.length} problemi`)

phase('Correzione')
const correzione = problemi.length === 0 ? null : await agent(`${CTX}
COMPITO: correggi sul ramo allenamento nel worktree ${WT} i problemi veri segnalati dai revisori, con una prova per ciascuno dove ha senso, e spiega quelli che respingi. Se i numeri cambiano, rilancia la taratura e aggiorna strumenti/taratura_allenamento.txt; se cambiano i suoni, aggiorna la collezione (sempre V204 se non pubblicata) e suoni_di_mess.txt. ruff, pytest, commit. Nelle note un riassunto in prosa per Gabriele: come si usa la sala allenamento tasto per tasto, come funzionano i contratti, dove cade la classe dei giocatori del suo mondo, e i numeri principali.
PROBLEMI: ${JSON.stringify(problemi)}
RAPPORTI: ${JSON.stringify({ cuore, finestra, taratura })}`, { label: 'correzione', phase: 'Correzione', schema: LAVORO_SCHEMA })

return { domande: [...bozza.domande_per_gabriele, ...progetto.domande_per_gabriele], progetto: progetto.progetto, cuore, finestra, taratura, problemi, correzione }
