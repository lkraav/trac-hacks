(function($) {
    var _ = (function() {
        var tx = babel.Translations;
        if (tx && tx.get) {
            var rv = tx.get('wikiganttchart-js');
            return function() {
                return rv.gettext.apply(rv, arguments);
            };
        }
        return window.gettext;
    })();
    var css = {minWidth: "20px", maxWidth: "80%", padding: "5px",
            borderRadius: "6px", border: "solid 1px #777",
            boxShadow: "4px 4px 4px #555", backgroundColor: "#fff",
            opacity: "1", zIndex: "32767", textAlign: "left"};
    $.balloon.defaults.css = css;
    $.balloon.defaults.classname = 'rmgantt-editor-balloon';

    var defaultOption = {
        withShow: true
        , viewMonths: 3
        , zoomScale: [0, 5, 8, 14, 20]
        , classes: 'rmgantt'
        , subjectWidth: 330
        , headerHeight: 24
        , headerMarginBottom: 4
        , lineHeightWithMargin: 26
        , linesHeightMargin: 150
        , linesMaxHeight: 206
        , ratioMargin: 6
        , appendingTaskCount: 3
        , indentIncrement: 10
        , leafColor: {
            blue: '#7DB5CF'
            , green: '#B4C880'
            , yellow: '#CFC47D'
            , red: '#CD9BA2'
            , purple: '#B1ADC2'
            , white: '#BBBBBB'
        }
        , parentColor: {
            blue: '#742933'
            , green: '#742933'
            , yellow: '#742933'
            , red: '#742933'
            , purple: '#742933'
            , white: '#742933'
        }
        , ratioColor: {
            blue: '#2B5C73'
            , green: '#486A34'
            , yellow: '#978200'
            , red: '#742933'
            , purple: '#4D3667'
            , white: '#4F4F4F'
        }
        , defaultColorStyle: 'blue'
        , editableDataParams: {}
        , cookieKey: 'TracWikiGanttChartMacro_VisibleCols_'
        , cookieKeyDateSpan: 'TracWikiGanttChartMacro_DateSpan_'
        , cookieExpires: 30
        , regional: {
            newTitle: _('New task')
            , updateTitle: _('Update task')
            , status: _('Status')
            , ticket: _('Ticket')
            , subject: _('Subject')
            , date: _('Date')
            , thisMonth: _('This Month')
            , startDate: _('Start Date')
            , dueDate: _('Due Date')
            , owner: _('Owner')
            , create: _('Create')
            , update: _('Update')
            , cancel: _('Cancel')
            , go: _('Go')
            , months: _('monthes')
            , color: _('Color')
            , style: _('Style')
            , progress: _('Progress')
            , dateError: _(' is not valid format for date.')
            , blue: _('blue')
            , green: _('green')
            , yellow: _('yellow')
            , red: _('red')
            , purple: _('purple')
            , white: _('white')
        }
        , onSave: function(successed, failed){}
    };

    // Utility functions.
    var util = {
    };

    var Gantt = (function(opt) {
        var gantt = function(dom, data, opt) {
            this.dom = dom;
            this.data = data;
            this._option = $.extend({}, this._default_opt);
            this.current = null;
            if($.isPlainObject(opt)) {
                this.extendOption(opt);
            }
            var cookieVal = $.cookie(this._option.cookieKey + this.elemId());
            if(cookieVal) {
                this.visibleCol = JSON.parse(cookieVal);
            } else {
                this.visibleCol = {
                    'start-date': false
                    , 'due-date': false
                    , 'owner': true
                };
            }
            var datespanCookieVal = $.cookie(this._option.cookieKeyDateSpan + this.elemId());
            if(datespanCookieVal) {
                try {
                    var data = JSON.parse(datespanCookieVal);
                    this.dateFrom = new XDate(data.startDate);
                    this._option.viewMonths = parseInt(data.viewMonths);
                } catch(e) {
                }
            }
        };

        gantt._key = '__rmgantt_object';

        gantt.isGantt = function(elem) {
            var dom = $(elem).get(0);
            var gdata = $.data(dom, this._key);
            return gdata instanceof this;
        };

        gantt.getGantt = function(elem) {
            var dom = $(elem).get(0);
            var gdata = $.data(dom, this._key);
            if(gdata instanceof this) {
                return gdata;
            } else {
                throw "This element dosen't have gantt data.";
            }
        };

        gantt.create = function(elem, data, opt) {
            var dom = $(elem).get(0);
            var gdata = new gantt(elem, data, opt);
            gdata._init();
            $.data(dom, this._key, gdata);
            return gdata;
        };

        $.extend(gantt.prototype, {
            _default_opt: opt
            , _elemIdPrefix: 'rmgantt-'

            , _init: function() {
                this.checkStyle();
                var d;
                if(this.dateFrom) {
                    d = this.dateFrom;
                } else {
                    d = new XDate.today();
                }
                this.setDate(d);
                this.tasks = new gantt.TreeData(this.data.tasks);
                this.initMenu();
                this.bindEvents();
                if(this._option.withShow) {
                    this.show();
                }
            }

            , updateData: function(data) {
                this.data = data;
                this.checkStyle();
                this.tasks.setTasks(this.data.tasks);
            }

            , checkStyle: function() {
                var inarray = false;
                var self = this;
                var keys = $.each(this._option.leafColor,
                    function(key, value) {
                        if(self.data.style == key) {
                            inarray = true;
                            return false;
                        }
                    });
                if(!inarray) {
                    this.data.style = this._option.defaultColorStyle;
                }
            }

            , setDate: function(d) {
                d.setDate(1).clearTime();
                this.dateFrom = d.clone();
                d.addMonths(this._option.viewMonths).setDate(0);
                this.dateTo = d.clone();
            }

            , extendOption: function(opt) {
                $.extend(this._option, opt);
            }

            , prev: function() {
                this.setDate(this.dateFrom.addMonths(-1));
                this.show();
            }

            , next: function() {
                this.setDate(this.dateFrom.addMonths(1));
                this.show();
            }

            , go: function(month, months) {
                this.setDate(month);
                if(months) {
                    this._option.viewMonths = months;
                }
                this.show();
            }

            , show: function() {
                this.clear();
                this.elem().append(this.render());
                var self = this;
                $.each(this.visibleCol, function(key, val) {
                    if(val) {
                        self.showColumn(key);
                    } else {
                        self.hideColumn(key);
                    }
                });
            }

            , save: function(saveAction) {
                var self = this;
                var tasks = this.tasks;
                var option = this._option;
                var successed = function(data) {
                    self.hideBalloonForce();
                    self.updateData(data);
                    self.show();
                };
                var failed = function(errorMsg) {
                    this.tasks = tasks;
                    this._option = option;
                    alert(errorMsg)
                };
                saveAction();
                var data = {
                    tasks: this.tasks.data()
                    , style: this.data.style
                    , id: this.data.id
                };
                this._option.onSave(data, successed, failed);
            }

            , createTicket: function(line) {
                var self = this;
                var tasks = this.tasks;
                var option = this._option;
                var successed = function(data) {
                    self.updateData(data);
                    self.show();
                };
                var failed = function(errorMsg) {
                    this.tasks = tasks;
                    this._option = option;
                    alert(errorMsg)
                };
                var data = {
                    tasks: this.tasks.data()
                    , style: this.data.style
                    , id: this.data.id
                };
                this._option.createTicket(data, line, successed, failed);
            }

            , clear: function() {
                this.elem().empty();
            }

            , render: function() {
                return $.render.gantt(
                    this.tplData(), this.tplHelper());
            }

            , elem: function() {
                return $(this.dom);
            }

            , tplData: function() {
                var style_vars = this.calcStyle();
                var basis = $.extend({}, style_vars, {
                    elemId: this.elemId()
                    , writable: this.data.writable
                    , regional: this._option.regional
                });

                var subjects =  this.subjects(basis);
                var months = this.months(basis);
                var days = this.days(basis);
                var today = this.today(basis);
                var lines = this.lines(basis);

                var year = this.dateFrom.getFullYear();
                var selectYear = []
                for(var y = year - 2; y <= year + 2; y++) {
                    selectYear.push({ year: y, selected: y == year });
                }
                var selectMonth = [];
                for(var m = 1; m <= 12; m++) {
                    selectMonth.push({ month: m, selected: (m == this.dateFrom.getMonth() + 1) });
                }

                return $.extend({}, basis, {
                    classes: this.classes()
                    , subjects: subjects
                    , months: months
                    , days: days
                    , today: today
                    , lines: lines
                    , tableTop: basis.headersHeight - this._option.lineHeightWithMargin * 2 - 2
                    , selectYear: selectYear
                    , selectMonth: selectMonth
                    , viewMonths: this._option.viewMonths
                });
            }

            , tplHelper: function() {
                return {};
            }

            , elemId: function() {
                return this._elemIdPrefix + this.data.id;
            }

            , classes: function() {
                return this._option.classes;
            }

            , numberOfLows: function() {
                return this.tasks.length();
            }

            , calcStyle: function() {
                if(this.data.zoom >= this._option.zoomScale.length) {
                    throw 'Invalid zoom value: ' + this.data.zoom;
                }
                var zoom = this._option.zoomScale[this.data.zoom];
                var subjectWidth = this._option.subjectWidth;
                var headerHeight = this._option.headerHeight;
                var headersHeight = headerHeight;
                var showWeeks = false;
                var showDays  = false;
                if(this.data.zoom > 1) {
                    //showWeeks = true;
                    //headersHeight = 2 * headerHeight;
                    if(this.data.zoom > 2) {
                        showDays = true;
                        headersHeight = 3 * headerHeight;
                    }
                }

                // Width of the entire chart
                var gWidth = (this.dateFrom.diffDays(this.dateTo) + 1) * zoom;
                var gHeight = Math.max(
                    this._option.lineHeightWithMargin *
                            (this.numberOfLows() + this._option.appendingTaskCount),
                    this._option.linesMaxHeight);
                var tHeight = gHeight + headersHeight;

                /*
                var span = 6;
                var smonth = this.dateFrom.clone().addMonths(-span);
                var monthSelect = [];
                for(var i = 0; i < span * 2 + 1; i++) {
                    var m = {month: smonth.toString('yyyy-MM')};
                    if(smonth.getMonth() == this.dateFrom.getMonth()) {
                        m.selected = true;
                    }
                    monthSelect.push(m);
                    smonth.addMonths(1);
                }
                */
                var styleSelect = [];
                var self = this;
                $.each(this._option.leafColor, function(style, color) {
                    var m = {style: style, color: color, name: self._option.regional[style]};
                    if(self.data.style == style) {
                        m.selected = true;
                    }
                    styleSelect.push(m);
                });

                return {
                    zoom: zoom
                    , subjectWidth: subjectWidth
                    , headerHeight: headerHeight
                    , headersHeight: headersHeight
                    , showDays: showDays
                    , showWeeks: false //showWeeks
                    , gWidth: gWidth
                    , gHeight: gHeight
                    , tHeight: tHeight
                    //, monthSelect: monthSelect
                    , styleSelect: styleSelect
                    , lineHeight: this._option.lineHeightWithMargin
                    , current: this.dateFrom.toString(_('MMMM, yyyy'))
                }
            }

            , subjects: function(base) {
                var self = this;
                return this.tasks.map(function(task, i) {
                    return $.extend({}, base, {
                        no: i
                        , indent: Array(task.level+1).join('&nbsp;&nbsp;')
                        , lineHeight: self._option.lineHeightWithMargin
                        , task: task
                        , data: task.data
                    });
                });
            }

            , months: function(base) {
                var monthF = this.dateFrom.clone();
                var left = 0;
                var height = base.headerHeight - 1;
                var months = [];
                for(var i = 0; i < this._option.viewMonths; i++) {
                    var md = monthF.clone().addMonths(1).setDate(0).getDate();
                    var width = (md * base.zoom) - 1;
                    months.push({
                        month: monthF.toString('yyyy-MM')
                        , title: monthF.toString('yyyy MMMM')
                        , left: left
                        , height: height
                        , width: width
                    });
                    monthF.addMonths(1);
                    left = left + width + 1;
                }
                return months;
            }

            , days: function(base) {
                if(base.showDays) {
                    var left = 0;
                    var width = base.zoom - 1;
                    var height = base.headerHeight;
                    var days = [];
                    var day = this.dateFrom.clone();
                    var diff = this.dateFrom.diffDays(this.dateTo) + 1;
                    for(var i = 0; i < diff; i++) {
                        var klass = 'gantt_hdr';
                        if($.inArray(day.getDay(), [1, 0]) >= 0) {
                            klass += " nwday";
                        }
                        days.push({
                            left: left
                            , top: this._option.headerHeight
                            , width: width
                            , height: height
                            , class_: klass
                            , day: [day.getDate(), this.getShortWeekday(day)]
                            , gHeight: base.gHeight + 1
                        });
                        left = left + width + 1;
                        day.addDays(1);
                    }
                    return days;
                } else {
                    return [];
                }
            }

            , today: function(base) {
                var today = XDate.today();
                if(today >= this.dateFrom && today <= this.dateTo) {
                    var todayLeft = this.dateFrom.diffDays(today) * base.zoom - 1;
                    return {
                        todayLeft: todayLeft
                    }
                } else {
                    return false;
                }
            }

            , lines: function(base) {
                var top_for_line = base.headersHeight + 2;
                var top_for_bar = this._option.headerMarginBottom;
                var self = this;
                return this.tasks.map(function(task, i) {
                    var coords = self.coordinates(
                        self.tasks.get(i).startDate, self.tasks.get(i).dueDate, undefined, base.zoom);
                    var klass = 'task';
                    var color;
                    if(self.tasks.get(i).children.length > 0) {
                        klass += ' parent';
                        color = self._option.parentColor[self.data.style];
                    } else {
                        klass += ' leaf';
                        color = self._option.leafColor[self.data.style];
                    }
                    width = coords.barEnd - coords.barStart - 1;
                    btop = top_for_bar + self._option.lineHeightWithMargin * i;
                    ltop = top_for_line + self._option.lineHeightWithMargin * i;
                    ratioWidth = null;
                    ratioLTop = null;
                    ratioColor = self._option.ratioColor[self.data.style];
                    if(task.ratio) {
                        ratioWidth = task.ratio / 100.0 * width;
                        ratioLTop = btop + self._option.ratioMargin/2;
                        btop = btop - self._option.ratioMargin/2;
                    }
                    return {
                        coords: coords
                        , task: task
                        , regional: self._option.regional
                        , no: i
                        , top: btop
                        , line_top: ltop
                        , class_: klass
                        , data: task.data
                        , width: width
                        , color: color
                        , ratio: task.ratio
                        , ratioWidth: ratioWidth
                        , ratioTop: ratioLTop
                        , ratioColor: ratioColor
                        , lineHeight: self._option.lineHeightWithMargin
                        , gWidth: base.gWidth
                    };
                });
            }

            , coordinates: function(startDate, dueDate, progress, zoom) {
                var coords = {};
                if(startDate && dueDate && startDate < this.dateTo && dueDate > this.dateFrom) {
                    if(startDate > this.dateFrom) {
                        coords.start = this.dateFrom.diffDays(startDate);
                        coords.barStart = this.dateFrom.diffDays(startDate);
                    } else {
                        coords.barStart = 0;
                    }
                    if(dueDate < this.dateTo) {
                        coords.end = this.dateFrom.diffDays(dueDate);
                        coords.barEnd = this.dateFrom.diffDays(dueDate) + 1;
                    } else {
                        coords.barEnd = this.dateFrom.diffDays(this.dateTo) + 1;
                    }
                }
                $.each(coords, function(key, value) {
                    coords[key] = Math.round(value) * zoom;
                });
                return coords;
            }

            , validate: function(data) {
                var error = [];
                if(!data.subjectName || data.subjectName == "") {
                    error.push(_('Subject is needed.'));
                }
                var self = this;
                $.each([['startDate', _('Start Date')], ['dueDate', _('Due Date')]],
                        function(_, val){
                            if(data[val[0]] != "" && !XDate.parse(data[val[0]])) {
                                error.push(val[1] + self._option.regional.dateError);
                            }
                        });
                if(XDate.parse(data.startDate) > XDate.parse(data.dueDate)) {
                    error.push(_('Start Date must be before due date'));
                }
                if(data.ratio && !data.ratio.match(/^((\d\d?)|100)$/)) {
                    error.push(_('Progress must be number between 0 and 100.'));
                }
                return error;
            }

            , saveVisibleColState: function(){
                $.cookie(this._option.cookieKey + this.elemId(),
                        JSON.stringify(this.visibleCol),
                        this._option.cookieExpires);
            }

            , saveDateSpan: function() {
                $.cookie(this._option.cookieKeyDateSpan + this.elemId(),
                        JSON.stringify({
                            startDate: this.dateFrom.toString('yyyy-MM-dd'),
                            viewMonths: this._option.viewMonths
                        }),
                        this._option.cookieExpires);
            }

            ///
            ///

            , bindEvents: function() {
                var self = this;
                var doc = $(document);
                var editor = "#" + this.elemId() + "-editor";
                var subjects = '#' + this.elemId() + ' td.subjects';

                $(editor + " .datepick").livequery(function() {
                    $(this).datepicker(wikiganttchart.datepicker);
                });

                doc.delegate('#' + this.elemId() + ' .to-prev', 'click', function(){
                    self.prev();
                    return false;
                });
                doc.delegate('#' + this.elemId() + ' .to-next', 'click', function(){
                    self.next();
                    return false;
                });
                doc.delegate('#' + this.elemId() + ' .to-this-month', 'click', function(){
                    self.go(new XDate());
                    return false;
                });
                doc.delegate('#' + this.elemId() + ' .select-style', 'change', function(){
                    var style = $(this).find(':selected').val();
                    self.save(function() {
                        self.data.style = style;
                    });
                    return false;
                });
                doc.delegate(editor + " .cancel", 'click', function() {
                    self.hideBalloon();
                });
                doc.delegate(editor + " form", 'submit', function() {
                    if(self._editor_callback) {
                        var data = {};
                        $.each($(this).serializeArray(), function(_, v){
                            data[v.name] = v.value;
                        });
                        var error = self.validate(data);
                        if(data.ratio) {
                            data.ratio = parseInt(data.ratio)
                        }
                        if(error.length > 0) {
                            alert(error.join("\n"));
                            return false;
                        }
                        self._editor_callback(data);
                        return false;
                    }
                });
                doc.delegate('#' + this.elemId() + ' :not(.rmgantt-editor-balloon)', 'click', function() {
                    if ($(this).parents('.rmgantt-editor-balloon').length == 0 &&
                        $(this).parents('.contextMenuPlugin').length == 0)
                    {
                        self.hideBalloon();
                    }
                });
                doc.delegate('#' + this.elemId() + ' .task-line', 'dblclick', function() {
                    var idx = parseInt($(this).attr('data-gantt-idx'));
                    self.editorAction('edit', idx);
                });
                doc.delegate('#' + this.elemId() + ' .task-line', 'mouseover', function(event) {
                    var idx = $(this).attr('data-gantt-idx');
                    var line = '#' + self.elemId() + ' .task-line[data-gantt-idx=' + idx + ']';
                    $(line).addClass('hover');
                    var tooltip = $(line + ' .rmgantt-tooltip').clone(true);
                    $('body').append(tooltip);
                    tooltip.css({left: event.pageX + 10, top: event.pageY + 10}).show();
                });
                doc.delegate('#' + this.elemId() + ' .task-line', 'mouseout', function() {
                    var idx = $(this).attr('data-gantt-idx');
                    var line = '#' + self.elemId() + ' .task-line[data-gantt-idx=' + idx + ']';
                    $(line).removeClass('hover');
                    $('body > .rmgantt-tooltip').remove();
                });
                doc.delegate(subjects + ' select.colmun-selecter', 'change', function(){
                    var name = $(this).find(':selected').val();
                    self.showColumn(name);
                    self.visibleCol[name] = true;
                    $(this).find(':selected').removeAttr('selected');
                    self.saveVisibleColState();
                });
                doc.delegate(subjects + ' .delete-btn', 'click', function(){
                    var name = $(this).attr('data-colname');
                    self.hideColumn(name);
                    self.visibleCol[name] = false;
                    self.saveVisibleColState();
                });
                doc.delegate('#' + this.elemId() + ' .date-selector', 'submit', function(){
                    var year = $(this).find('[name="year"]').val();
                    var month = $(this).find('[name="month"]').val();
                    var months = $(this).find('[name="months"]').val();

                    if(parseInt(months) > 0) {
                        self._option.viewMonths = months;
                        self.go(new XDate(year, month-1, 1), months);
                        self.saveDateSpan();
                    }
                    return false;
                });
            }

            , initMenu: function() {
                var id = "#" + this.elemId();
                var tasks = this.tasks;
                var self = this;
                if(this.data.writable) {
                    $(id + " .chart td.subjects").livequery(function(){
                        var elem = $(this);
                        $(this).contextPopup({
                            items: [
                                {
                                    label: _('Insert')
                                    , action: function() {
                                        self.editorAction('new');
                                        return false;
                                    }
                                    , icon: 'fa-file-o'
                                }
                            ]
                        });
                    });
                    $(id + " .task-line").livequery(function(){
                        var idx = parseInt($(this).attr('data-gantt-idx'));
                        var col = this;
                        $(this).contextPopup({
                            items: [
                                {
                                    label: _('Edit task')
                                    , action: function() {
                                        self.editorAction('edit', idx);
                                        return false;
                                    }
                                    , icon: 'fa-edit'
                                }
                                , {
                                    label: _('Delete task')
                                    , action: function() {
                                        self.save(function(){
                                            tasks.destroy(idx);
                                        });
                                        return false;
                                    }
                                    , icon: 'fa-trash-o'
                                }
                                , {
                                    label: _('Insert task'),
                                    action: function() {
                                        self.editorAction('insertBelow', idx);
                                        return false;
                                    }
                                    , icon: "icon-task"
                                }
                                , {
                                    label:_('Insert subtask')
                                    , action:function() {
                                        self.editorAction('insertChild', idx);
                                        return false;
                                    }
                                    , icon: "icon-subtask"
                                    , separation: true
                                }
                                , {
                                    label: _('Up')
                                    , action: function() {
                                        self.save(function(){
                                            tasks.moveUp(idx);
                                        });
                                        return false;
                                    }, isEnabled: function() {
                                        return !tasks.isOldest(idx);
                                    }
                                }
                                , {
                                    label: _('Down')
                                    , action: function() {
                                        self.save(function(){
                                            tasks.moveDown(idx);
                                        });
                                        return false;
                                    }
                                    , isEnabled: function() {
                                        return !tasks.isYoungest(idx);
                                    }
                                }
                                , {
                                    label: _('Level up')
                                    , action: function() {
                                        self.save(function(){
                                            tasks.shiftLeft(idx);
                                        });
                                        return false;
                                    }
                                    , isEnabled: function() {
                                        return tasks.get(idx).level != 1;
                                    }
                                    , icon: 'fa-outdent'
                                }
                                , {
                                    label: _('Level down')
                                    , action: function() {
                                        self.save(function(){
                                            tasks.shiftRight(idx);
                                        });
                                        return false;
                                    }
                                    , isEnabled: function() {
                                        return !tasks.isOldest(idx) &&
                                            tasks.get(idx).level != self.maxLevel;
                                    }
                                    , icon: 'fa-indent'
                                    , separation: true
                                }
                                , {
                                    label: _('Create ticket')
                                    , action: function() {
                                        self.createTicket(idx);
                                        return false;
                                    }
                                    , isEnabled: function() {
                                        return !tasks.get(idx).data.linkToTicket &&
                                            self.data.ticketCreatable;
                                    }
                                    , icon: 'fa-plus'
                                }
                            ]
                        });
                    });
                }
            }

            , showColumn: function(name) {
                var subjects = '#' + this.elemId() + ' td.subjects';
                $(subjects + ' .' + name).removeClass('hidden');
                this.redraw();
            }

            , hideColumn: function(name) {
                var subjects = '#' + this.elemId() + ' td.subjects';
                $(subjects + ' .' + name).addClass('hidden');
                this.redraw();
            }

            , showEditor: function(target, task, callback) {
                var data = {
                    regional: this._option.regional
                    , elemId: this.elemId()
                    , task: task ? task : {
                            startDate: null
                            , dueDate: null
                            , data: {
                                subjectName: null
                                , owner: null
                            }
                            , ratio: null
                        }
                    , isnew: task ? false : true
                };
                var form = $.render['gantt-editor'](data, this.tplHelper());
                var self = this;
                this.toggleBalloon($(target), {contents: form});
                this._editor_callback = callback;
                setTimeout(function() {
                        $('.rmgantt.gantt-editor input[name="subjectName"]').focus();
                    }, 500);
            }

            , hideBalloon: function() {
                if(this.current) {
                    this.current.hideBalloon();
                }
                this.current = null;
            }

            , hideBalloonForce: function() {
                $('.rmgantt-editor-balloon, .balloon').hide();
                this.current = null;
            }

            , toggleBalloon: function(target, opts) {
                this.hideBalloon();
                if (this.current && this.current[0] === target[0]) {
                    this.current = null;
                    return;
                }
                if (target.position().top - $(window).scrollTop() < 100)
                    opts.position = 'bottom';
                else
                    opts.position = 'top';
                if (target.position().left - $(window).scrollLeft() < 100)
                    opts.position = 'mid right';
                else if (target.position().left + target.width() - $(window).scrollLeft() > $(window).width() - 100)
                    opts.position = 'mid left';
                this.current = target;
                target.showBalloon(opts);
            }

            , editorAction: function(action, idx) {
                if(!this.data.writable) {
                    return false;
                }
                var self = this;
                var id = '#' + this.elemId();
                var tasks = this.tasks;
                var col;
                if(action == 'new') {
                    col = $(id + ' td.subjects');
                } else {
                    col = $(id + ' .issue-subject[data-gantt-idx=' + idx + ']');
                }
                var task = null;
                if(action == 'edit') {
                    task = tasks.get(idx);
                }
                var actionList = {
                    edit: function(data) {
                        tasks.updateTask(idx, data);
                    }
                    , 'new': function(data) {
                        tasks.insert(data);
                    }
                    , insertAbove: function(data) {
                        tasks.insertAbove(data, idx);
                    }
                    , insertBelow: function(data) {
                        tasks.insertBelow(data, idx);
                    }
                    , insertChild: function(data) {
                        tasks.insertChild(data, idx);
                    }
                };
                self.showEditor(col, task, function(data) {
                    self.save(function() {
                        actionList[action](data);
                    });
                    return true;
                });
                return true;
            }

            , redraw: function() {
                var subjects = $('#' + this.elemId() + ' td.subjects');
                var table = $('#' + this.elemId() + ' td.subjects > table');
                subjects.css('width', table.width());

                var subjects = '#' + this.elemId() + ' td.subjects ';
                $(subjects + ' .colmun-selecter option[value]').each(function() {
                    var name = $(this).val();
                    if(!$(subjects + ' thead th[data-colname="' + name + '"]').hasClass('hidden')) {
                        $(this).attr('disabled', 'disabled');
                    } else {
                        $(this).removeAttr('disabled');
                    }
                });
            }

            , getShortWeekday: function(dat) {
                var weekdays = wikiganttchart.datepicker.dayNamesMin;
                var indexes = {Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6};
                var idx = indexes[dat.toString('ddd')];
                return weekdays[idx];
            }
        });

        gantt.TreeData = (function() {
            var tree = function(tasks) {
                this._genTree(tasks);
                this._calcTaskStartEnd();
            };

            $.extend(tree.prototype, {
                length: function() {
                    return this.tasks.length;
                }

                , get: function(idx) {
                    return this.tasks[idx];
                }

                , getParent: function(idx) {
                    return this.get(this.get(idx).parentIdx);
                }

                , each: function(f) {
                    $.each(this.tasks, f);
                }

                , map: function(f) {
                    return $.map(this.tasks, f);
                }

                , getSiblings: function(idx) {
                    var task = this.get(idx);
                    return task.level == 1 ?
                        this._rootc : this.getParent(idx).children;
                }

                , getRank: function(idx) {
                    var task = this.get(idx);
                    return $.inArray(task, this.getSiblings(idx));
                }

                , isOldest: function(idx) {
                    return this.getRank(idx) == 0;
                }

                , isYoungest: function(idx) {
                    return this.getRank(idx) == this.getSiblings(idx).length - 1;
                }

                , getOlder: function(idx) {
                    var sib = this.getSiblings(idx);
                    return sib[this.getRank(idx) - 1].no;
                }

                , moveUp: function(idx) {
                    this.swap(idx, this.getOlder(idx));
                }

                , moveDown: function(idx) {
                    var sib = this.getSiblings(idx);
                    this.swap(idx, sib[this.getRank(idx) + 1].no);
                }

                , shiftLeft: function(idx) {
                    var task = this.get(idx);
                    var parent = task.parentIdx;
                    this._drop(idx);
                    this.getSiblings(parent).splice(
                            this.getRank(parent) + 1, 0, task);
                    this.reindex();
                }

                , shiftRight: function(idx) {
                    var task = this.get(idx);
                    var older = this.getOlder(idx);
                    this._drop(idx);
                    this.get(older).children.push(task);
                    this.reindex();
                }

                , destroy: function(idx) {
                    this._drop(idx);
                    this.reindex();
                }

                , _drop: function(idx) {
                    this.getSiblings(idx).splice(this.getRank(idx), 1);
                }

                , swap: function(a, b) {
                    var siblA = this.getSiblings(a);
                    var rankA = this.getRank(a);
                    var taskA = this.get(a);
                    var siblB = this.getSiblings(b);
                    var rankB = this.getRank(b);
                    var taskB = this.get(b);

                    siblA[rankA] = taskB;
                    siblB[rankB] = taskA;

                    this.reindex();
                }

                , updateTask: function(idx, data) {
                    task = this.get(idx);
                    this._setTaskData(task, data);
                    this.reindex();
                }

                , insert: function(data) {
                    var task = {};
                    this._setTaskData(task, data);
                    var rootlen = this._rootc.length;
                    this._rootc.splice(rootlen + 1, 0, task);
                    this.reindex();
                }

                , insertChild: function(data, idx) {
                    var task = {};
                    this._setTaskData(task, data);
                    this.get(idx).children.push(task);
                    this.reindex();
                }

                , insertAbove: function(data, idx) {
                    var task = {};
                    this._setTaskData(task, data);
                    this.getSiblings(idx).splice(this.getRank(idx), 0, task);
                    this.reindex();
                }

                , insertBelow: function(data, idx) {
                    var task = {};
                    this._setTaskData(task, data);
                    this.getSiblings(idx).splice(this.getRank(idx) + 1, 0, task);
                    this.reindex();
                }

                , _setTaskData: function(task, data) {
                    if(task.children == undefined) {
                        task.children = [];
                    }
                    task.savedStartDate = data.startDate
                    task.savedDueDate = data.dueDate
                    task.ratio = data.ratio
                    task.data = {
                        subjectName: data.subjectName
                        , ticket: data.ticket
                        , owner: data.owner ? data.owner.split(',') : ""
                    };
                }

                , traceTree: function(f) {
                    var tracer;
                    tracer = function(task, parent) {
                        f(task, parent);
                        $.each(task.children, function(_, c){
                            tracer(c, task);
                        });
                    };
                    $.each(this._rootc, function(_, c) {
                        tracer(c, null);
                    });
                }

                , reindex: function() {
                    var idx = 0;
                    var newtree = [];
                    this.traceTree(function(task, parent) {
                        task.no = idx ++;
                        task.parentIdx = parent ? parent.no : null;
                        task.level = parent ? parent.level + 1 : 1;
                        newtree.push(task);
                    });
                    this.tasks = newtree;
                    this._calcTaskStartEnd();
                }

                , data: function() {
                    var data = [];
                    this.traceTree(function(task, parent) {
                        data.push({
                            level: task.level
                            , parent: task.parentIdx
                            , startDate: task.savedStartDate
                            , dueDate: task.savedDueDate
                            , data: task.data
                            , ratio: task.ratio
                        });
                    });
                    return data;
                }

                , setTasks: function(tasks) {
                    this._genTree(tasks);
                    this._calcTaskStartEnd();
                }

                , _genTree: function(tasks) {
                    var tpdata = $.map(tasks, function(task, i) {
                        return {
                            no: i
                            , level: task.level
                            , parentIdx: task.parent
                            , children: []
                            , savedStartDate: task.startDate
                            , savedDueDate: task.dueDate
                            , startDatePrintable: task.startDatePrintable
                            , dueDatePrintable: task.dueDatePrintable
                            , startDatePrintableLong: task.startDatePrintableLong
                            , dueDatePrintableLong: task.dueDatePrintableLong
                            , data: $.extend({}, task.data)
                            , color: task.color
                            , style: task.style
                            , ratio: task.ratio
                        };
                    });
                    var rootc = [];
                    $.each(tpdata, function(i, task) {
                        if(task.parentIdx == null) {
                            if(task.level != 1) {
                                throw 'Invalid level value. index: ' + i;
                            }
                            rootc.push(task);
                        } else {
                            var parent = tpdata[task.parentIdx];
                            if(parent === undefined) {
                                // Child's index must be bigger than parent's one.
                                throw 'Invalid parent value. index: ' + i;
                            }
                            if(parent.level != task.level - 1) {
                                throw 'Invalid level value. index: ' + i;
                            }
                            parent.children.push(task);
                        }
                    });
                    this.tasks = tpdata;
                    this._rootc = rootc;
                }

                , _calcTaskStartEnd: function() {
                    var self = this;
                    var rev_tasks = $.merge([], this.tasks);
                    rev_tasks.sort(function(a, b){
                        return b.level - a.level;
                    });
                    if(rev_tasks.length > 0) {
                        this.maxLevel = rev_tasks[0].level;
                    }
                    $.each(rev_tasks, function(_, rtask) {
                        rtask.startDate =
                            rtask.savedStartDate ? new XDate(rtask.savedStartDate) : null;
                        rtask.dueDate =
                            rtask.savedDueDate ? new XDate(rtask.savedDueDate) : null;
                        $.each(rtask.children, function(_, child) {
                            var setDate = function(d, f) {
                                if(!rtask[d] || f(rtask[d], child[d])) {
                                    rtask[d] = child[d];
                                }
                            }
                            setDate('startDate', function(a, b) { return a > b; });
                            setDate('dueDate', function(a, b) { return a < b });
                        });
                    });
                }
            });

            return tree;
        })();

        return {
            isGantt: gantt.isGantt
            , getGantt: gantt.getGantt
            , create: gantt.create
        };
    })(defaultOption);

    $.rmgantt = function(elem, cmd, args) {
        switch(cmd) {
        default:
            throw "Unknown command: " + cmd;
        }
    };

    $.fn.rmgantt = function(data, opts) {
        this.each(function() {
            Gantt.create(this, data, opts);
        });
        return this;
    };

})(jQuery)
