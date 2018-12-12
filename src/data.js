(function(){

    class PoEData {

        constructor() {
            this.data = {};

            this.pendingLoads = [];
            this.activeLoad = undefined;
        }

        initialize() {
            this.initializeUI();
        }

        initializeUI() {
            $('#settingsDataReload').click(function(){
                POEI.data.reload();
            })
        }

        update(delta) {
            if(this.activeLoad === undefined && this.pendingLoads.length > 0){
                this.activeLoad = this.pendingLoads.pop();
                $.getJSON('https://cors.io/?' + this.activeLoad[1], {type: this.activeLoad[0]}, function (e) {
                    POEI.data.processData(e);
                }).fail(function() {
                    POEI.data.retryActiveLoad();
                });
            }
        }

        reload() {
            // Special case for maps, comes in 2 different urls
            this.pendingLoads.push([ItemTypeEnum.Map, this.getApiLink('Map'), 0]);

            for(let type in ItemTypeEnum) {
                let typeValue = ItemTypeEnum[type];

                let url = this.getApiLink(typeValue);
                this.pendingLoads.push([typeValue, url, 0]);
            }
        }

        retryActiveLoad() {
            if(this.activeLoad !== undefined){
                this.activeLoad[2]++;
                if(this.activeLoad[2] < 3) {
                    console.log("Data Retry: " + this.activeLoad[0] + ' ' + (this.activeLoad[2] + 1) + ' / 3');

                    this.pendingLoads.push(this.activeLoad);
                    this.activeLoad = undefined;
                } else {
                    console.warn("Data Failed: " + this.activeLoad[0]);
                    this.activeLoad = undefined;
                }
            }
        }

        processData(rawData) {
            let type = this.activeLoad[0];

            if(rawData === undefined
                || rawData.lines === undefined) {
                console.log('Unknown data for ' + type);
                this.activeLoad = undefined;
                return;
            }

            console.log('Processing Data for ' + type);

            this.data[type] = {
                raw: rawData
            };

            let lines = rawData.lines;
            console.log('  --> L = ' + lines.length);

            switch (type) {
                case ItemTypeEnum.Currency:
                case ItemTypeEnum.Fragment:
                {
                    let currencyDetails = rawData.currencyDetails;
                    console.log('  --> C = ' + currencyDetails.length);

                    for(let i in currencyDetails) {
                        this.processCurrencyEntry(type, currencyDetails[i]);
                    }
                }
            }

            for(let i in lines) {
                let line = lines[i];
                this.processDataEntry(type, line);
            }

            this.activeLoad = undefined;
        }

        processCurrencyEntry(type, currencyInfo) {

            let entry = {
                id: currencyInfo.id,
                name: currencyInfo.name,
                tradeId: currencyInfo.poeTradeId,
                icon: currencyInfo.icon,
                raw: currencyInfo
            };

            if(entry.id === undefined
                || entry.id === ""
                || entry.name === undefined
                || entry.name === ""){
                console.log('Invalid Currency Data: ');
                console.log(currencyInfo);
                return;
            }

            this.data[type][entry.name] = entry;
        }

        processDataEntry(type, dataEntry) {

            let entry = {
                id: undefined,
                raw: dataEntry
            };

            // Fill the main data
            switch (type) {
                case ItemTypeEnum.Currency:
                case ItemTypeEnum.Fragment:
                {
                    entry = this.data[type][dataEntry.currencyTypeName];
                    if(entry === undefined){
                        console.error("Currency is missing Base Entry: " + dataEntry.currencyTypeName);
                        return;
                    }

                    entry.id = dataEntry.currencyTypeName;
                    entry.name = dataEntry.currencyTypeName;
                    entry.type = type;
                    entry.value = dataEntry.chaosEquivalent || 0;
                    entry.pay = dataEntry.pay;
                    entry.receive = dataEntry.receive;

                    break
                }

                default: {
                    entry.id = dataEntry.id;
                    entry.name = dataEntry.name;
                    entry.icon = dataEntry.icon;
                    entry.value = dataEntry.chaosValue || 0;
                    entry.modsImplicit = dataEntry.implicitModifiers || [];
                    entry.modsExplicit = dataEntry.explicitModifiers || [];
                    entry.corrupted = dataEntry.corrupted || false;
                    entry.iType = dataEntry.itemType;
                    entry.iClass = dataEntry.itemClass;
                    entry.flavor = dataEntry.flavourText;

                    if(entry.iType === "Unknown") {
                        entry.iType = undefined;
                    }

                    if(dataEntry.variant !== undefined
                        && dataEntry.variant !== ''
                        && dataEntry.variant !== null) {
                        entry.variant = dataEntry.variant;
                    }

                    break;
                }
            }

            // Special fields per type
            switch (type) {
                case ItemTypeEnum.Armor:
                case ItemTypeEnum.Weapon: {
                    entry.links = dataEntry.links || 0;
                    break
                }

                case ItemTypeEnum.Map: {
                    entry.tier = dataEntry.mapTier;
                    entry.baseType = dataEntry.baseType;

                    break;
                }

                case ItemTypeEnum.Gem: {
                    entry.tier = dataEntry.gemLevel || 0;
                    entry.quality = dataEntry.gemQuality || 0;

                    break;
                }
            }

            if(entry.id === undefined
                || entry.id === ""
                || entry.name === ""
                || entry.name === undefined
                || entry.value === undefined
                || entry.value === "") {
                console.warn("Invalid Data: ");
                console.log(entry);
                return;
            }

            switch (type) {
                case ItemTypeEnum.Currency:
                case ItemTypeEnum.Fragment: {
                    return;
                }
            }

            if(this.data[type][entry.name] !== undefined){
                if(this.data[type][entry.name].variants === undefined) {
                    this.data[type][entry.name].variants = [];
                }

                // Add this item as a sub-variant
                this.data[type][entry.name].variants.push(entry);
                return;
            }

            this.data[type][entry.name] = entry;
        }

        getApiLink(type) {

            let apiFunc = 'itemoverview';
            switch (type) {
                case ItemTypeEnum.Currency:
                case ItemTypeEnum.Fragment: {
                    apiFunc = 'currencyoverview';
                    break
                }
            }

            return Constants.NinjaAPI + apiFunc + "?league=" + Constants.League + "&type=" + type + "&date=" + moment().format("YYYY-MM-DD");
        }

        getData(type, id) {
            if(this.data[type] === undefined || id === undefined) {
                return undefined;
            }

            let searchId = id;
            switch (type) {
                case ItemTypeEnum.Gem:
                {
                    searchId = searchId.replace('Vaal ', '');
                    break;
                }

                case ItemTypeEnum.Map:
                {
                    searchId = searchId.replace('Superior ', '');
                    break;
                }
            }

            return this.data[type][searchId];
        }
    }

    POEI.data = new PoEData();

})();