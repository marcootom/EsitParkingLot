function connectToPark(){
    //Viene creato un client AWS tramite l'utilizzo dell'endpoint e viene richiesto l'utilizzo del servizio IotData
    let iotData = new AWS.IotData({
        endpoint: 'a3cytfxnue36h3-ats.iot.us-west-2.amazonaws.com',
        region: 'us-west-2',
        accessKeyId: 'AKIA437IIVU7BJX7RJFX',
        secretAccessKey: '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'
    })

    //Viene recuperata la sezione HTML denominata "all_parks"
    let invisible_class = document.getElementById('all_parks').innerHTML;

    /*Viene creato un array contenente tutti i parcheggi creati in precedenza attraverso il metodo split
    * utilizzato sulla stringa ottenuta tramite l'unione di tutti i parcheggi presenti nel database
    * separati da / */
    let parks = invisible_class.split('/');


    // Per ogni parcheggio presente nell'array
    for (let i = 0; i < parks.length; i++) {
        console.log(parks[i]);

        // Vengono settati i parametri che verranno poi passati al metodo GetThingShadow
        let params = {
            thingName: parks[i].trim(),
        };

        /* Attraverso il metodo GetThingShadow vengono richieste le variazioni di stato della shadow
        * corrispondente al parcheggio preso in esame */
        iotData.getThingShadow(params, function (err, data) {
            if (err) {
                console.log(err, err.stack); // an error occurred
                console.log(err.name)
            } else {
                // Viene preparato il json con i dati presenti all'interno della sezione "metadati"
                let tmp = data.payload.split(',"metadata"');
                tmp = tmp[0] + "}";

                let json = JSON.parse(tmp.toString());

                // Value = nome del parcheggio
                let value = parks[i];
                value = value.replace(/\s/g, '');
                // Viene recuperato il numero di stalli presenti nel parcheggio
                console.log(json);
                let length = json.state.reported.s.length;

                // Viene recuperata l'area HTML destinata al parcheggio
                document.getElementById('park-content-' + parks[i].trim()).innerHTML = "";

                /* In questa sezione viene generato il layout in base alle informazioni ottenute in tempo reale da
                * AWS come il numero degli stalli, il loro stato (libero oppure occupato) ecc.*/
                let div1 = document.createElement('div');
                div1.classList.add("inside-park");
                let div2 = document.createElement('div');
                div2.classList.add("card-body");
                div2.classList.add("mt-3");
                let div3 = document.createElement('div');
                div3.classList.add("card");
                div3.classList.add("border-primary");
                let div4 = document.createElement('div');
                div4.classList.add("card-body");
                let div5 = document.createElement('div');
                div5.classList.add("modal-body");
                let link = document.createElement('a');
                /*In questo modo viene creato un collegamento tramite il nome del parcheggio alla pagina
                * "single_park_info" la quale permette di controllare un parcheggio e i suoi stalli nello specifico*/
                link.setAttribute('href', '/park/' + value)
                let div6 = document.createElement('p');
                div6.id = "park_title";
                div6.innerHTML = value;

                link.append(div6);
                div5.append(link);

                // Creazione della sezione per il monitoraggio degli stalli
                let stall = []; //stalli presenti all'interno del dato parcheggio
                let state = []; //stato dello stallo preso in esame
                for (let j = 0; j < length; j++) {
                    stall[j] = JSON.stringify(json.state.reported.s[j].id);
                    state[j] = JSON.stringify(json.state.reported.s[j].v);
                    var div_stall = document.createElement('div');
                    div_stall.classList.add("card");
                    div_stall.classList.add("border-primary");
                    div_stall.classList.add("card-padding");
                    var div_stall2 = document.createElement('div');
                    div_stall2.classList.add("card-body");
                    var div_stall3 = document.createElement('div');
                    div_stall3.id = "stalli" + stall[j] + value;

                    div_stall2.append(div_stall3);
                    div_stall.append(div_stall2);
                    div5.append(div_stall)
                }
                div4.append(div5);
                div3.append(div4);
                div2.append(div3);
                div1.append(div2);
                document.getElementById('park-content-'+ parks[i].trim()).append(div1);

                /* In questa sezione viene settato lo stato degli stalli: nel caso in cui lo stato dello stallo
                * ottenuto dalla shadow dovesse essere pari a 1 allora lo stallo è libero e apparirà di colore verde,
                * in caso contrario apparirà di colore rosso */
                for (let j = 0; j < length; j++) {
                    document.getElementById('stalli' + stall[j] + value).innerHTML = "Stall: " + stall[j];
                    let dot = document.createElement('span');
                    dot.id = "dot-" + stall[j] + value;
                    document.getElementById('stalli' + stall[j] + value).append(dot);
                    if (state[j] === '1') {
                        document.getElementById('dot-' + stall[j] + value).style.backgroundColor = "green";
                    } else {
                        document.getElementById('dot-' + stall[j] + value).style.backgroundColor = "red";
                    }
                }
            }
        });
    }
}
//Ad un intervallo di tempo prefissato viene rieseguita la funzione "connectToPark" per aggiornare la situazione stalli
setInterval(connectToPark, 2000);
