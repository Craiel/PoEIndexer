(function(){

    const TimerCallback = function(source, delta) {
        POEI.events.update(delta);
    };

    class PoEIndexerEvents {

        constructor() {
        }

        initialize() {
            this.initializeUI();

            POEI.createInterval('events', TimerCallback, 500);

            this.refreshEvents();
        }

        initializeUI() {
        }

        refreshEvents() {
        }

        update(delta) {

            let time = moment();
            this.updateTime('time-local', time);
        }

        updateTime(elementId, time){
            $('#' + elementId + '-hours').text(time.format('HH'));
            $('#' + elementId + '-min').text(time.format('mm'));
            $('#' + elementId + '-sec').text(time.format('ss'));
        }
    }

    POEI.events = new PoEIndexerEvents();

})();