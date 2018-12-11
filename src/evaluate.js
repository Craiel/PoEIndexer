(function(){

    class PoEIndexerEvaluate {

        constructor() {
            this.statMissingData = 0;

            this.statEval = 0;
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

            this.statEval++;
            $('#statEval').text(this.statEval + ' Eval');

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

                    entry.rawData = data;
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

        evaluateEntry(entry, data) {
            entry.eval = {
                // TODO
            };

            let variant = data;
            if(data.variants !== undefined) {
                variant = this.determineMatchingVariant(entry, data);
                if(variant === undefined){
                    return;
                }
            }

            if(data.value <= entry.cost
                || data.value < Constants.EvalMinValue) {
                // No gain
                return;
            }

            // TODO further evaluate
            entry.eval.grosGain = data.value - entry.cost;

            if(entry.eval.grosGain < Constants.EvalMinGrosGain) {
                // not enough gain
                return;
            }

            POEI.results.add(entry, data);
        }

        determineMatchingVariant(entry, data) {
            console.warn("Unhandled Variant for " + entry.name);
            return undefined;
        }
    }

    POEI.evaluate = new PoEIndexerEvaluate();

})();