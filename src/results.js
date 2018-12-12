(function(){

    class PoEIndexerResults {

        constructor() {
            this.entries = [];
            this.entryMap = {};
            this.entryIdMap = {};
            this.nextId = 0;
            this.targetElement = undefined;
        }

        initialize() {
            this.targetElement = $('#result-table');
        }

        update(delta) {
        }

        add(entry) {
            if(this.entryIdMap[entry.raw.id] !== undefined) {
                // TODO: Refresh!
                return;
            }

            entry.resultId = this.nextId++;
            let row = $('<tr data-status="' + entry.type + '" id="result-' + entry.resultId + '"></tr>');

            let linkColumn = $('<td><a type="button" class="btn btn-primary resultLink" id="copyResult-' + entry.resultId + '" href="#">Copy</a></td>');
            row.append(linkColumn);

            let iconColumn = $('<td><img class="result-icon" src="' + entry.icon + '"/></td>');
            row.append(iconColumn);

            let contentColumn = $('<td class="w-100"></td>');
            row.append(contentColumn);

            let contentBody = $('<div class="result-content-body"></div>');
            let content = $('<div class="result-content"></div>');
            content.append(contentBody);
            contentColumn.append(content);

            contentBody.append($('<h4 class="title">' + entry.name + '<span class="float-right result-type result-' + entry.type + '"></span></h4>'));

            let detailList = $('<table class="table"></table>');
            detailList.append($('<tr><td>Cost</td><td>' + entry.cost +'</td></tr>'));
            detailList.append($('<tr><td>Value</td><td>' + entry.data.value +'</td></tr>'));
            detailList.append($('<tr><td>Gros Gain</td><td>' + entry.eval.grosGain +'</td></tr>'));
            detailList.append($('<tr><td>Net Gain</td><td>' + entry.eval.netGain +'</td></tr>'));
            detailList.append($('<tr><td>Pay in</td><td>' + entry.costAd +' ' + entry.costCurrencyAd + '</td></tr>'));
            contentBody.append(detailList);

            this.entries.push(entry);
            this.entryMap[entry.resultId] = entry;
            this.entryIdMap[entry.raw.id] = entry;

            while(this.entries.length > 50) {
                let oldEntry = this.entries.shift();
                $('#result-' + oldEntry.resultId).remove();
                delete this.entryMap[oldEntry.resultId];
                delete this.entryIdMap[oldEntry.raw.id];
            }

            this.targetElement.prepend(row);

            POEI.stats.add('Results');
        }

        copyResultLink(id) {
            let entry = this.entryMap[id];
            console.log(entry);

            let link = '@' + entry.character + ' Hi, I would like to buy your ' + entry.name +
                ' listed for ' + entry.costAd + ' ' + entry.costCurrencyAd + ' in ' + Constants.League +
                ' (stash tab "' + entry.stash + '"; position: left ' + entry.pos[0] + ', top ' + entry.pos[1] + ')';

            console.log(link);

            POEI.copyText(link, 'Copy');
        }
    }

    $(document).ready(function() {
        $('body').on('click', 'a.resultLink', function() {
            let idSegments = this.id.split('-');
            POEI.results.copyResultLink(idSegments[1]);

            $(this).text('Copied');
        });
    });

    POEI.results = new PoEIndexerResults();

})();