(function(){

    const autoSave = function(){
        POEI.settings.save();
    };

    class PoEIndexerSettings {

        constructor() {
            // Volatile settings, not saved
            this.loadedVersion = 0;
            this.awayTime = undefined;
        }

        initialize() {
            this.load();

            POEI.createInterval("Auto-save", autoSave, 5000);
        }

        load() {
            let rawData = localStorage.getItem(Constants.SettingsKey);
            if(rawData === undefined || rawData === null) {
                return;
            }

            let data = JSON.parse(rawData);
            if(data === undefined || data === null) {
                return;
            }

            this.loadedVersion = data.version;

            if(data.lastVisited !== undefined) {
                this.awayTime = (Date.now() - data.lastVisited) / 1000;
            }
        }

        save() {
            let data = {
                version: Constants.SettingsVersion,
                lastVisited: Date.now()
            };

            localStorage.setItem(Constants.SettingsKey,JSON.stringify(data));
        }


    }

    POEI.settings = new PoEIndexerSettings();

})();