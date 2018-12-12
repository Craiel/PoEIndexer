(function(){

    class PoEIndexerStats {

        constructor() {
            this.entries = {}
        }

        initialize() {
        }

        add(key, value) {
            if(value === undefined) {
                value = 1;
            }

            if(this.entries[key] === undefined) {
                this.entries[key] = {
                    id: 'stat-' + key,
                    val: 0
                };

                $('#navStats').append($('<li class="nav-item"><div id="' + this.entries[key].id + '">' + key + ': N/A</div></li>'));
            }

            this.entries[key].val += value;
            $('#' + this.entries[key].id).text(key + ': ' + this.entries[key].val);
        }
    }

    POEI.stats = new PoEIndexerStats();

})();