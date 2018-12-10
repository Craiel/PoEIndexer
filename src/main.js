let POEI = (function(){

    class PoEIndexer {

        constructor() {
            this.intervals = {};
            this.lastUpdateTime = 0;
        }

        createInterval(name, callback, delay, data) {
            this.intervals[name] = {c: callback, d: delay, e: 0, data: data}
        }

        removeInterval(name) {
            delete this.intervals[name];
        }

        showCopyLinkDialog(path, title) {
            let link = "";
            if(window.location.origin !== null && window.location.origin !== "null") {
                link = window.location.origin;
            } else {
                link = 'file://';
            }

            this.showCopyTextDialog(link + window.location.pathname + path, title);
        }

        showCopyTextDialog(text, title){
            $('#copyTextModalTitle').text(title);
            $('#copyTextModal-text').val(text);
            $('#copyTextModal').modal();
        }

        initializeUI() {
            for(let content in ContentTypeEnum) {
                $('#' + ContentTypeEnum[content]).hide();

                let contentToggle = $('#' + ContentTypeEnum[content] + '_toggle');
                contentToggle.click({id: ContentTypeEnum[content]}, function(e) {
                    POEI.activateContent(e.data.id);
                });

                contentToggle.removeClass('active');
            }

            $('#copyTextModal-copy').click(function(e){
                $('#copyTextModal-text').select();
                document.execCommand("copy");
                $('#copyTextModal').modal('toggle');
            });
        }

        initializeSystems() {

            POEI.settings.initialize();
            POEI.changeLog.initialize();
            POEI.events.initialize();
            POEI.data.initialize();
            POEI.stash.initialize();
            POEI.evaluate.initialize();

            feather.replace();
        }

        initialize() {

            this.initializeUI();

            this.initializeSystems();

            this.activateContent(ContentTypeEnum.Main);

            window.requestAnimationFrame(POEI.updateFrame);
        }

        updateFrame(time) {
            let delta = time - POEI.lastUpdateTime;
            if (delta > 1000 / (Constants.FPS || 10)) {
                POEI.update(delta);
                POEI.lastUpdateTime = time;
            }

            window.requestAnimationFrame(POEI.updateFrame);
        }

        update(delta) {
            for (let name in this.intervals) {
                let interval = this.intervals[name];
                interval.e += delta;
                if (interval.e > interval.d) {
                    interval.c(this, interval.e / 1000, interval.data);
                    interval.e = 0;
                }
            }

            this.data.update(delta);
            this.stash.update(delta);
            this.evaluate.update(delta);
        }

        activateContent(type) {
            if(this.activeContent !== undefined) {
                $('#' + this.activeContent).hide();
                $('#' + this.activeContent + '_toggle').removeClass('active');

                if(this.activeContent === ContentTypeEnum.AreaMap && this.activeArea !== undefined) {
                    this.areas[this.activeArea].deactivate();
                }
            }

            this.activeContent = type;
            $('#' + type).show();

            $('#' + type + '_toggle').addClass('active');
        }

    }

    return new PoEIndexer();

})();