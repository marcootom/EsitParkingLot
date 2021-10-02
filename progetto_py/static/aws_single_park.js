/*Il funzionamento di questo script è praticamente identico allo script aws_park, la differenza sostanziale sta
* nella generazione dell'html in quanto in questo caso verrà riprodotto un unico parcheggio (il parcheggio su cui
* è stato effettuato il click) con i suoi relativi stalli. Per il resto non vi sono particolari variazioni.*/

function connectToPark() {

    let iotData = new AWS.IotData({
        endpoint: '',
        region: 'us-west-2',
        accessKeyId: '',
        secretAccessKey: ''
    })

    // Viene recuperato il nome del parcheggio.
    let thingName = document.getElementById('park_title').innerHTML;

    // Vengono settati i parametri da passare alla funzione "getThingShadow" per recuperare i dati da AWS
    let params = {
        thingName: thingName,
    };

    iotData.getThingShadow(params, function (err, data) {
        if (err) {
            console.log(err, err.stack); // an error occurred
        } else {
            console.log(data);
            let tmp = data.payload.split(',"metadata"');
            tmp = tmp[0] + "}";

            let json = JSON.parse(tmp.toString());
            let length = json.state.reported.s.length;

            document.getElementById('park-content').innerHTML = "";
            let page = document.createElement('div');
            page.classList.add("row");

            // Vengono creati gli stalli
            let stall = [];
            let state = [];
            for (let i = 0; i < length; i++) {
                stall[i] = JSON.stringify(json.state.reported.s[i].id);
                state[i] = JSON.stringify(json.state.reported.s[i].v);
                let div_stall = document.createElement('div');
                div_stall.classList.add("card");
                div_stall.classList.add("border-primary");
                div_stall.classList.add("card-padding-single");
                let div_stall2 = document.createElement('div');
                div_stall2.classList.add("card-body");
                let div_stall3 = document.createElement('div');
                div_stall3.id = "stalli" + stall[i];

                div_stall2.append(div_stall3);
                div_stall.append(div_stall2);
                page.append(div_stall)
            }

            // Vengono assegnati in tempo reale i valori agli stalli del parcheggio
            document.getElementById('park-content').append(page);
            for (let i = 0; i < length; i++) {
                document.getElementById('stalli' + stall[i]).innerHTML = "Stall: " + stall[i];
                let dot = document.createElement('span');
                dot.id = "dot-" + stall[i];
                document.getElementById('stalli' + stall[i]).append(dot);
                if (state[i] === '1') {
                    document.getElementById('dot-' + stall[i]).style.backgroundColor = "green";
                } else {
                    document.getElementById('dot-' + stall[i]).style.backgroundColor = "red";
                }
            }
        }
    });
}

setInterval(connectToPark, 3000);