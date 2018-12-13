(function(){

    class PoEIndexerEvaluate {

        constructor() {
            this.variantMap = {
                atziriSplendor: {
                    'Armour': '{}% increased armour',
                    'Armour/ES': '{}% increased armour and energy shield',
                    'Armour/Evasion': '{}% increased armour and evasion',
                    'Armour/Evasion/ES': '{}% increased armour, evasion and energy shield',
                    'ES': '+{} to maximum energy shield',
                    'Evasion': '{}% increased evasion rating',
                    'Evasion/ES': '{}% increased evasion and energy shield',
                },

                doryaniInvitation: {
                    'Fire': '{}% increased fire damage',
                    'Cold': '{}% increased cold damage',
                    'Lightning': '{}% increased lightning damage',
                    'Physical': '{}% increased global physical damage',
                },

                impresence: {
                    'Chaos': 'adds {} to {} chaos damage',
                    'Fire': 'adds {} to {} fire damage',
                    'Cold': 'adds {} to {} cold damage',
                    'Lightning': 'adds {} to {} lightning damage',
                    'Physical': 'adds {} to {} physical damage',
                },

                vesselVinktar: {
                    'Added Attacks': 'adds {} to {} lightning damage to attacks during flask effect',
                    'Added Spells': 'adds {} to {} lightning damage to spells during flask effect',
                    'Conversion': '{}% of physical damage converted to lightning during flask effect',
                    'Penetration': 'damage penetrates {}% lightning resistance during flask effect',
                },

                yrielFostering: {
                    'Maim': 'grants level {} summon bestial rhoa skill',
                    'Bleeding': 'grants level {} summon bestial ursa skill',
                    'Poison': 'grants level {} summon bestial snake skill',
                },

                volkuurGuidance: {
                    'Fire': 'adds {} to {} fire damage to spells and attacks',
                    'Cold': 'adds {} to {} cold damage to spells and attacks',
                    'Lightning': 'adds {} to {} lightning damage to spells and attacks',
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
                        POEI.stats.add('Missing Data');
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

            POEI.stats.add('Eval');

            entry.eval = {
                // TODO
            };

            entry.data = this.determineMatchingVariant(entry);
            if(entry.data === undefined) {
                POEI.stats.add('Eval Invalid');
                return;
            }

            if(entry.data.value === undefined
                || entry.data.value <= entry.cost
                || entry.data.value < Constants.EvalMinValue) {
                // No gain
                POEI.stats.add('Eval Low Gain');
                return;
            }

            // TODO further evaluate
            entry.eval.grosGain = Math.floor(entry.data.value - entry.cost);
            entry.eval.grosGainPc = Math.round((entry.eval.grosGain / entry.data.value) * 100);

            if(entry.eval.grosGainPc < Constants.EvalMinGrosGainPc
                || entry.eval.grosGain < Constants.EvalMinGrosGain) {
                // not enough gain
                POEI.stats.add('Eval Low Gain');
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

            let results = [];

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
                                results.push(varData);
                            }
                        } else {
                            // This data is for specific amount of links
                            if(entry.highestLink === varData.links) {
                                results.push(varData);
                            }
                        }
                    }

                    if(results.length === 1) {
                        return results[1];
                    }

                    if(results.length > 1) {
                        console.log(entry);
                        console.log(variants);
                        console.log(results);
                        throw TODO_ARMOR_TOO_MANY_MATCHES
                    }

                    return undefined;
                }

                case ItemTypeEnum.Gem: {
                    // Quality + Level

                    let level = parseInt(entry.properties.Level[0][0].replace(' (Max)', ''));
                    let quality = 0;
                    if(entry.properties.Quality !== undefined) {
                        quality = parseInt(entry.properties.Quality[0][0].replace('+', '').replace('%', ''));
                    }

                    switch (entry.name) {
                        case 'Empower Support':
                        case 'Enhance Support':
                        case 'Enlighten Support': {
                            // Special gems that we care about in any case
                            break;
                        }

                        default: {
                            // For random gems we have to have at least 20 in something
                            if(level < 20 && quality < 20) {
                                // At least one of the values has to be max for us to even consider
                                return undefined;
                            }
                        }
                    }

                    for(let i in variants) {
                        let varData = variants[i];
                        let varQ = varData.quality;
                        let varL = varData.tier;

                        if(varQ === quality
                            && varL === level) {
                            results.push(varData);
                        }
                    }

                    if(results.length === 1) {
                        return results[1];
                    }

                    if(results.length > 1) {
                        console.log(entry);
                        console.log(variants);
                        console.log(results);
                        throw TODO_GEM_TOO_MANY_MATCHES
                    }

                    return undefined;
                }

                case ItemTypeEnum.Jewel:
                case ItemTypeEnum.Accessory:
                case ItemTypeEnum.Flask: {
                    if(variants.length === 1) {
                        return variants[0];
                    }

                    console.error("Unhandled Variants: ");
                    console.log(entry);
                    console.log(variants);
                    return undefined;
                }

                default: {
                    if(variants.length > 1){
                        console.warn("Unhandled Variant for " + entry.name + ' || ' + entry.type);
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

                if(varData.corrupted === true
                    && entry.corrupted !== true) {
                    // Separate corrupted data from non-corrupted results
                    continue;
                }

                if(varData.variant !== undefined) {
                    // Variant special cases

                    // Special cases by variant
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

                    // Special cases by name
                    switch (varData.name) {
                        case 'Atziri\'s Splendour': {
                            matchRequired = true;

                            if (this.itemHasExplicit(entry, this.variantMap.atziriSplendor[varData.variant])) {
                                entry.variantNote = varData.variant;
                                return [varData];
                            }

                            continue;
                        }

                        case 'Doryani\'s Invitation': {
                            matchRequired = true;

                            if (this.itemHasExplicit(entry, this.variantMap.doryaniInvitation[varData.variant])) {
                                entry.variantNote = varData.variant;
                                return [varData];
                            }

                            continue;
                        }

                        case 'Impresence': {
                            matchRequired = true;

                            if (this.itemHasExplicit(entry, this.variantMap.impresence[varData.variant])) {
                                entry.variantNote = varData.variant;
                                return [varData];
                            }

                            continue;
                        }

                        case 'Vessel of Vinktar': {
                            matchRequired = true;

                            if (this.itemHasExplicit(entry, this.variantMap.vesselVinktar[varData.variant])) {
                                entry.variantNote = varData.variant;
                                return [varData];
                            }

                            continue;
                        }

                        case 'Yriel\'s Fostering': {
                            matchRequired = true;

                            if (this.itemHasExplicit(entry, this.variantMap.yrielFostering[varData.variant])) {
                                entry.variantNote = varData.variant;
                                return [varData];
                            }

                            continue;
                        }

                        case 'Volkuur\'s Guidance': {
                            matchRequired = true;

                            if (this.itemHasExplicit(entry, this.variantMap.volkuurGuidance[varData.variant])) {
                                entry.variantNote = varData.variant;
                                return [varData];
                            }

                            continue;
                        }
                    }

                    result.push(varData);

                } else {

                    // Base type special cases
                    switch (varData.name) {

                        // These items have the same properties but differ in base type
                        case 'Doryani\'s Delusion':
                        case 'Combat Focus':
                        case 'Grand Spectrum':
                        case 'Precursor\'s Emblem': {
                            matchRequired = true;

                            if (varData.raw.baseType === entry.typeLine) {
                                entry.variantNote = 'BaseType = ' + varData.raw.baseType;
                                return [varData];
                            }

                            break;
                        }

                        default: {
                            result.push(varData);
                            break;
                        }
                    }
                }
            }

            if(matchRequired && result.length === 0) {
                console.error("Variant Mismatch: ");
                console.log(entry);
                console.log(variants);
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