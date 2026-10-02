# Istruzioni per ClaudIA sull'altra macchina

Scritte il 2026-10-02 dalla sessione dell'ufficio, cartella utente C:\Users\GBattaglia. Quando sei allineata, cancella questo file, committa e pubblica.

## Dove sta lo stato del lavoro

Piano di sviluppo, CHANGELOG.md e storia dei commit bastano: il 2026-10-02 sono state chiuse la tappa 0, col punto 0.4, e la tappa 1, col banco strumenti/banco_partite.py e il rapporto di riferimento strumenti/banco_partite_prima.txt. Il prossimo passo del piano è la tappa 2.

## L'unica cosa che git non porta

E:\git\mine\projects.json non è sotto git, quindi sull'altra macchina non ha la modifica di oggi. La voce Showdown deve diventare così, aggiungendola intera se manca:

    "Showdown": {
        "description": "MESS Manager e Simulatore Showdown",
        "script": "Showdown.py",
        "version": "1.0.0"
    }

Il file di avvio si chiamerà Showdown.py, con la maiuscola: lo ha deciso Gabriele il 2026-10-02, e il piano è già corretto.

## Scelte di oggi che non stanno scritte altrove

La tappa 1 non ha alzato la versione: il banco è uno strumento di sviluppo e il programma non cambia. Gabriele può ancora decidere di farla contare come 1.1.0.
