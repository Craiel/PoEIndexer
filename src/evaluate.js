(function(){

    class PoEIndexerEvaluate {

        constructor() {
            this.statMissingData = 0;

            this.statEval = 0;

            this.variantMap = {
                'atziriSplendor': {
                    'Armour': '{}% increased armour',
                    'Armour/ES': '{}% increased armour and energy shield',
                    'Armour/Evasion': '{}% increased armour and evasion',
                    'Armour/Evasion/ES': '{}% increased armour, evasion and energy shield',
                    'ES': '+{} to maximum energy shield',
                    'Evasion': '{}% increased evasion rating',
                    'Evasion/ES': '{}% increased evasion and energy shield',
                }
            };
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

            switch (entry.type) {
                // For now ignore certain things
                case ItemTypeEnum.Currency: {
                    return;
                }
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
                    this.evaluateEntry(entry);
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
            entry.eval = {
                // TODO
            };

            entry.data = this.determineMatchingVariant(entry);
            if(entry.data === undefined) {
                return;
            }

            if(entry.data.value === undefined
                || entry.data.value <= entry.cost
                || entry.data.value < Constants.EvalMinValue) {
                // No gain
                return;
            }

            // TODO further evaluate
            entry.eval.grosGain = Math.floor(entry.data.value - entry.cost);
            entry.eval.grosGainPc = Math.round((entry.eval.grosGain / entry.data.value) * 100);

            if(entry.eval.grosGainPc < Constants.EvalMinGrosGainPc
                || entry.eval.grosGain < Constants.EvalMinGrosGain) {
                // not enough gain
                return;
            }

            POEI.results.add(entry);
        }

        determineMatchingVariant(entry) {
            let variants = [];
            variants.push(entry.rawData);
            if(entry.rawData.variants !== undefined) {
                for(let i in entry.rawData.variants) {
                    variants.push(entry.rawData.variants[i]);
                }
            }

            variants = this.filterVariantsBySpecial(entry, variants);

            switch (entry.type) {
                case ItemTypeEnum.Weapon:
                case ItemTypeEnum.Armor:{

                    if(entry.corrupted === true) {
                        // Won't deal with corrupted weapons + armor
                        return undefined;
                    }

                    // Sockets & Links
                    for(let i in variants) {
                        let varData = variants[i];

                        if(varData.links === undefined
                            || varData.links === 0) {

                            if(entry.highestLink === undefined
                                || entry.highestLink < 5) {

                                // This data can match, no links or not enough on either side
                                return varData;
                            }
                        } else {
                            // This data is for specific amount of links
                            if(entry.highestLink === varData.links) {
                                return varData;
                            }
                        }
                    }

                    //console.log(entry);
                    //throw TODO_ARMOR_NO_MATCH

                    return undefined;
                }

                case ItemTypeEnum.Gem: {
                    // Quality + Level
                    //console.log(entry);
                    //throw TODO_GEM_NO_MATCH

                    return undefined;
                }

                default: {
                    if(variants.length > 1){
                        console.warn("Unhandled Variant for " + entry.name);
                        return undefined;
                    }

                    break;
                }
            }
        }

        filterVariantsBySpecial(entry, variants) {
            let matchRequired = false;
            let result = [];
            for(let i in variants) {
                let varData = variants[i];

                if(varData.variant === undefined){
                    result.push(varData);
                    continue;
                }

                // Generic variants first
                switch (varData.variant) {
                    case '1 Jewel': {
                        if (entry.abyssSockets === 1) {
                            result.push(varData);
                        }

                        continue;
                    }

                    case '2 Jewels': {
                        if (entry.abyssSockets === 2) {
                            result.push(varData);
                        }

                        continue;
                    }
                }

                // Special cases
                switch (varData.name) {
                    case 'Atziri\'s Splendour': {
                        matchRequired = true;

                        console.log('ATZIRI: ' + varData.variant + ' (' + variants.length + ')');
                        if(this.itemHasExplicit(entry, this.variantMap.atziriSplendor[varData.variant])) {
                            return varData;
                        }
                    }
                }
            }

            if(matchRequired && result.length === 0) {
                console.error("Variant Mismatch: ");
                console.log(entry.explicits);
                //console.log(entry);
                //throw e;
            }

            return result;
        }

        itemHasExplicit(entry, explicit) {
            if(explicit === undefined
                || entry.explicits === undefined
                || entry.explicits.length === 0) {
                return false;
            }

            for(let i in entry.explicits) {
                if(entry.explicits[i] === explicit.toLowerCase().trim()) {
                    return true;
                }
            }

            return false;
        }
    }

    POEI.evaluate = new PoEIndexerEvaluate();

})();