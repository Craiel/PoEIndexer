(function(){

    class PoEIndexerStash {

        constructor() {
            this.currentChangeId = undefined;
            this.activeStashRequest = undefined;

            this.statStashes = 0;
            this.statItems = 0;
            this.delay = 0;
            this.isPaused = true;

            this.priceRegex = new RegExp('.*?~(b\\/o|price)\\s*([0-9\.]*)\\s*(\\w+)', 'i');
        }

        initialize() {
            $('#settingsPause').click(function(){
                POEI.stash.togglePause();
            });

            $.getJSON('https://cors.io/?http://poe.ninja/api/Data/GetStats', function (e) {
                POEI.stash.currentChangeId = e.next_change_id;
            }).fail(function() {
                console.error("Failed to get Current Stash ID");
            });
        }

        togglePause() {
            this.isPaused = !this.isPaused;
        }

        update(delta) {
            if(this.currentChangeId === undefined
                || this.isPaused === true) {
                return;
            }

            if(this.delay > 0) {
                this.delay -= delta;
                console.log(this.delay + ' || ' + delta);
                return;
            }

            // TODO
            if(this.activeStashRequest === undefined) {
                this.activeStashRequest = 'https://cors.io/?http://www.pathofexile.com/api/public-stash-tabs?id=' + this.currentChangeId;
                $.getJSON(this.activeStashRequest, function (e) {
                    POEI.stash.processStashes(e);
                }).fail(function() {
                    console.error("Failed to get Stash Data");
                    POEI.stash.delay = 5;
                    POEI.activeStashRequest = undefined;
                });
            }
        }

        processStashes(data) {
            this.currentChangeId = data.next_change_id;

            for(let i in data.stashes){
                let stash = data.stashes[i];
                if(stash === undefined
                    || stash.public !== true
                    || stash.league !== Constants.League
                    || stash.items === undefined
                    || stash.items.length === 0) {
                    // Not valid data
                    continue;
                }

                this.processStash(stash);
                this.statStashes++;
            }

            $('#statStashes').text(this.statStashes + ' Stashes');
            $('#statItems').text(this.statItems + ' Items');
            this.activeStashRequest = undefined;
        }

        processStash(stashData) {
            switch (stashData.stashType) {
                case 'CurrencyStash':
                case 'EssenceStash':
                case 'MapStash':
                case 'DivinationCardStash':
                case 'FragmentStash': {
                    // Ignore certain tabs for now
                    return;
                }
            }

            let isGlobalPrice = true;
            let globalPriceFixed = false;
            let globalPrice = 0;
            let globalPriceCurrency = undefined;

            let match = this.priceRegex.exec(stashData.stash);
            if(match !== null) {
                isGlobalPrice = true;

                if(match[1] === 'price') {
                    globalPriceFixed = true;
                }

                globalPrice = match[2];
                globalPriceCurrency = match[3];
            }

            for(let i in stashData.items) {
                let itemData = stashData.items[i];

                if(itemData.category === undefined){
                    console.warn("Item has no Category");
                    console.log(itemData);
                    continue;
                }

                let item = {
                    account: stashData.accountName,
                    pos: [itemData.w, itemData.h],
                    name: itemData.name,
                    icon: itemData.icon,
                    typeLine: itemData.typeLine,
                    frameType: itemData.frameType,
                    ident: itemData.identified === true,
                    properties: itemData.properties,
                    sockets: itemData.sockets,
                    stash: stashData.stash,
                    stashType: stashData.stashType,
                    raw: itemData
                };

                if(isGlobalPrice === true) {
                    item.costFixed = globalPriceFixed;
                    item.cost = globalPrice;
                    item.costCurrency = globalPriceCurrency;
                }

                let itemNote = itemData.note;
                if(itemNote !== undefined) {
                    let match = this.priceRegex.exec(itemNote);
                    if (match !== null) {
                        item.costFixed = match[1] === 'price';
                        item.cost = match[2].trim();
                        if (item.cost === '') {
                            item.cost = 1;
                        }

                        item.costCurrency = match[3];
                    }
                }

                if(item.cost === undefined) {
                    continue;
                }

                item.type = this.getItemTypeForCategory(itemData.category);

                switch (item.type) {
                    case ItemTypeEnum.Currency:
                    case ItemTypeEnum.Gem:
                    case ItemTypeEnum.Map:
                    case ItemTypeEnum.Card:
                    case ItemTypeEnum.Essence: {
                        item.name = item.typeLine;
                        break;
                    }
                }

                if(this.normalizeEntryCost(item) !== true) {
                    continue;
                }

                if(this.isValidItem(item)) {
                    this.statItems++;
                    POEI.evaluate.enqueue(item);
                }
            }
        }

        isValidItem(entry) {
            if(entry.name === ""
                || entry.name === undefined
                || entry.type === undefined) {
                return false;
            }

            for(let i in Constants.ItemIgnoreFilter) {
                if (entry.name.includes(Constants.ItemIgnoreFilter[i])) {
                    return false;
                }
            }

            return true;
        }

        getItemTypeForCategory(category){
            let categoryKey = Object.keys(category)[0];
            let value = category[categoryKey];

            switch (categoryKey) {
                case 'gems': {
                    return ItemTypeEnum.Gem;
                }

                case 'armour': {
                    return ItemTypeEnum.Armor;
                }

                case 'weapons': {
                    return ItemTypeEnum.Weapon;
                }

                case 'jewels': {
                    return ItemTypeEnum.Jewel;
                }

                case 'maps': {
                    if(value[1] === 'scarab') {
                        return ItemTypeEnum.Scarab;
                    }

                    return ItemTypeEnum.Map;
                }

                case 'accessories': {
                    return ItemTypeEnum.Accessory;
                }

                case 'flasks': {
                    return ItemTypeEnum.Flask;
                }

                case 'currency': {
                    switch (value[0]) {
                        case 'resonator': {
                            return ItemTypeEnum.Resonator;
                        }

                        case 'fossil': {
                            return ItemTypeEnum.Fossil;
                        }
                    }

                    return ItemTypeEnum.Currency;
                }

                case 'cards': {
                    return ItemTypeEnum.Card;
                }

                default: {
                    console.warn("Unhandled Category: " + category);
                    return undefined;
                }
            }
        }

        normalizeEntryCost(entry) {
            if(entry.cost === 0
                || entry.cost === ''
                || entry.cost === undefined
                || entry.costCurrency === undefined
                || entry.costCurrency === '') {
                return false;
            }

            let convertToChaos = true;
            let currencyId = entry.costCurrency;
            switch (entry.costCurrency.toLowerCase().trim()) {
                case 'alt': {
                    currencyId = 'Orb of Alteration';
                    break;
                }

                case 'jew': {
                    currencyId = 'Jeweller\'s Orb';
                    break;
                }

                case 'fuse': {
                    currencyId = 'Orb of Fusing';
                    break;
                }

                case 'chisel': {
                    currencyId = 'Cartographer\'s Chisel';
                    break;
                }

                case 'chrom': {
                    currencyId = 'Chromatic Orb';
                    break;
                }

                case 'silver': {
                    currencyId = 'Silver Coin';
                    break;
                }

                case 'alch':
                case 'alc':
                case 'alchemy': {
                    currencyId = 'Orb of Alchemy';
                    break;
                }

                case 'c':
                case 'chaos': {
                    currencyId = 'Chaos Orb';
                    convertToChaos = false;
                    break;
                }

                case 'vaal': {
                    currencyId = 'Vaal Orb';
                    break;
                }

                case 'scour': {
                    currencyId = 'Orb of Scouring';
                    break;
                }

                case 'regret': {
                    currencyId = 'Orb of Regret';
                    break;
                }

                case 'regal': {
                    currencyId = 'Regal Orb';
                    break;
                }

                case 'exa':
                case 'exalt': {
                    currencyId = 'Exalted Orb';
                    break;
                }

                case 'gcp': {
                    currencyId = 'Gemcutter\'s Prism';
                    break;
                }
            }

            let currencyData = POEI.data.getData(ItemTypeEnum.Currency, currencyId);
            if(currencyData === undefined) {
                console.error("Unknown Currency: " + currencyId);
                return false;
            }

            // Save the original cost info
            entry.costAd = entry.cost;
            entry.costCurrencyAd = entry.costCurrency;

            // Replace the currency with the proper id and save the original notation for the whisper url
            entry.costCurrency = currencyId;

            if(convertToChaos === true) {
                if(currencyData.value === undefined){
                    console.error("Currency has no Value: " + currencyId);
                    return false;
                }

                entry.cost = entry.cost * currencyData.value;
                entry.costCurrencyId = entry.costCurrency;
                entry.costCurrency = 'Chaos Orb';
            }

            return true;
        }
    }

    POEI.stash = new PoEIndexerStash();

})();