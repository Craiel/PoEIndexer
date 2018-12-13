(function(){

    class PoEIndexerStats {

        constructor() {
            this.entries = {}
        }

        initialize() {
        }

        add(key, value, parent) {
            if(value === undefined) {
                value = 1;
            }

            let id = 'stat-' + key.replace(/\s/g, '-').toLowerCase();
            if(this.entries[id] === undefined) {
                this.entries[id] = {
                    id: id,
                    val: 0
                };

                let parentEl = $('#navStatsSys');
                if(parent !== undefined) {
                    parentEl = $('#' + parent);
                }

                parentEl.append($('<li class="nav-item"><div id="' + id + '">' + key + ': N/A</div></li>'));
            }

            this.entries[id].val += value;
            $('#' + id).text(key + ': ' + this.entries[id].val);
        }
    }

    POEI.stats = new PoEIndexerStats();

})();