(function(){

    class PoEIndexerEvaluate {

        constructor() {
            this.statMissingData = 0;

            this.testCount = 0;
        }

        initialize() {
        }

        update(delta) {
        }

        enqueue(entry) {
            // TODO

            if(entry.name === undefined){
                console.warn("Item has no Name")
                console.log(entry);
                return;
            }

            this.testCount++;
            if(this.testCount > 50000){
                throw asdasd;
            }

            // 0 - Normal (Maps & Currency
            // 1 - Magic
            // 2 - Rare
            // 3 - Unique
            // 4 - Gems
            // 5 - Essences & Resonators
            // 6 - Prophecies
            // 8 - Prophecies
            switch (entry.frameType) {
                case 1: {
                    return;
                }

                case 2: {
                    // TODO: Yellow / Rare item support
                    return;
                }

                case 0:
                case 3:
                case 4:
                case 5:
                case 6:
                case 8: {
                    let data = POEI.data.getData(entry.type, entry.name);
                    if(data === undefined){
                        this.statMissingData++;
                        $('#statMissingData').text(this.statMissingData + ' Missing Data');
                        return;
                    }

                    this.evaluateEntry(entry, data);
                    return;
                }

                default: {
                    console.log("Check_frame_type");
                    console.log(entry);
                    break;
                }
            }
        }

        evaluateEntry(entry) {

        }
    }

    POEI.evaluate = new PoEIndexerEvaluate();

})();