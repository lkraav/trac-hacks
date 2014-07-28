$.templates("gantt-editor", "<div id=\"{{>elemId}}-editor\" class=\"rmgantt gantt-editor\">\n {{if isnew}}\n <h3 class=\"new\">{{>regional.newTitle}}</h3>\n {{else}}\n <div class=\"title\">\n <h3 class=\"edit\">{{>regional.updateTitle}}</h3>\n <div>\n {{if task.data.ticket}}\n {{:task.data.linkToTicket}}\n {{/if}}\n </div>\n </div>\n {{/if}}\n <form action=\"\" method=\"post\" onsubmit=\"return false;\">\n <div>\n <table>\n <tbody>\n <tr>\n <th><label>{{>regional.subject}}: </label></th>\n <td class=\"fullrow\" colspan=\"2\">\n <input type=\"text\" name=\"subjectName\" {{if !isnew}}value=\"{{>task.data.subjectName}}\"{{/if}} />\n </td>\n </tr>\n <tr>\n <th class=\"col1\"><label>{{>regional.owner}}: </label></th>\n <td class=\"col1\" colspan=\"2\"><input type=\"text\" name=\"owner\" {{if !isnew}}value=\"{{>task.data.owner}}\"{{/if}} /></td>\n </tr>\n <tr>\n <th class=\"col1\"><label>{{>regional.date}}: </label></th>\n <td class=\"col1\"><input type=\"text\" name=\"startDate\" class=\"date datepick\" type=\"text\" {{if !isnew}}value=\"{{>task.savedStartDate}}\"{{/if}} /></td>\n <td class=\"col2\"><input type=\"text\" name=\"dueDate\" class=\"date datepick\" type=\"text\" {{if !isnew}}value=\"{{>task.savedDueDate}}\"{{/if}} /></td>\n </tr>\n <tr>\n <th class=\"col1\"><label>{{>regional.progress}}: </label></th>\n <td class=\"col1\" colspan=\"2\"><input type=\"number\" max=\"100\" min=\"0\" name=\"ratio\" class=\"ratio\" {{if !isnew}}value=\"{{>task.ratio}}\"{{/if}} />%</td>\n </tr>\n <tr>\n <th class=\"col1\"><label>{{>regional.ticket}}: </label></th>\n <td class=\"col1\" colspan=\"2\"><span class=\"input-implant\" data-implant=\"#\"><input type=\"text\" name=\"ticket\" class=\"ticket\" {{if !isnew}}value=\"{{>task.data.ticket}}\"{{/if}} /></span></td>\n </tr>\n <tr>\n <td colspan=\"3\" div class=\"buttons\">\n {{if isnew}}\n <input type=\"submit\" value=\"{{>regional.create}}\" name=\"submit\" />\n {{else}}\n <input type=\"submit\" value=\"{{>regional.update}}\" name=\"submit\" />\n {{/if}}\n <input type=\"button\" value=\"{{>regional.cancel}}\" name=\"cancel\" class=\"cancel\" />\n </td>\n </tr>\n </tbody>\n </table>\n </div>\n </form>\n</div>\n");$.templates("gantt-lines", "{{if coords.barStart !== undefined && coords.barEnd !== undefined}}\n<div style=\"top:{{>top}}px; left:{{>coords.barStart}}px; width:{{>width}}px; background-color:{{>color}};\" class=\"task_todo {{>class_}}\">\n</div>\n{{if ratio}}\n<div style=\"top:{{>ratioTop}}px; left:{{>coords.barStart}}px; width:{{>ratioWidth}}px; background-color:{{>ratioColor}};\" class=\"task_todo ratio {{>class_}}\">\n</div>\n{{/if}}\n<div style=\"top:{{>top}}px; left:{{>coords.barStart}}px; width:{{>width}}px;\" class=\"label {{>class_}}\">\n {{>data.subjectName}}{{if ratio}}({{>ratio}}%){{/if}}\n</div>\n{{/if}}");$.templates("gantt-popup", "<div class=\"rmgantt-tooltip\">\n <h5>{{if task.data.ticket}}{{:task.data.linkToTicket}} {{/if}}{{>task.data.subjectName}}</h5>\n <dl>\n <dt>{{>regional.owner}}</dt>\n <dd>\n {{if data.owner}}\n {{>data.owner.join(',')}}\n {{/if}}\n </dd>\n <dt>{{>regional.date}}</dt>\n <dd>\n {{if task.startDate || task.dueDate}}\n {{>task.startDatePrintableLong}} ~ {{>task.dueDatePrintableLong}}\n {{/if}}\n </dd>\n <dt>{{>regional.progress}}</dt>\n <dd>\n {{if task.ratio}}\n {{>task.ratio}} %\n {{/if}}\n </dd>\n </dl>\n</div>");$.templates("gantt-subjects", "<tr id=\"{{>elemId}}-{{>no}}\" class=\"issue-subject task-line\" data-gantt-idx=\"{{>no}}\">\n <td class=\"subject-index\" style=\"height: {{>lineHeight}}px;\">\n {{>no+1}}\n </td>\n <td class=\"subject-name\" style=\"height: {{>lineHeight}}px;\" title=\"{{>data.subjectName}}\">\n {{: indent}}\n {{if data.linkToTicket}}\n {{: data.linkToTicket}}\n {{else}}\n <!--<a href=\"{{:hrefToCreateTicket}}\" class=\"create-ticket\">Create Ticket</a>-->\n {{/if}}\n {{>data.subjectName}}\n </td>\n <td class=\"start-date hidden\" style=\"height: {{>lineHeight}}px;\">\n {{>task.startDatePrintable}}\n </td>\n <td class=\"due-date hidden\" style=\"height: {{>lineHeight}}px;\">\n {{>task.dueDatePrintable}}\n </td>\n <td class=\"owner\" style=\"height: {{>lineHeight}}px;\">\n {{if data.owner}}\n <span class=\"owner-icon\">\n {{>data.owner.join(',')}}\n </span>\n {{/if}}\n </td>\n</tr>");$.templates("gantt", "<div id=\"{{>elemId}}\" class=\"{{>classes}} rmgantt\">\n <div class=\"header\">\n <div>\n <h3>{{>current}}</h3>\n <form action=\"#{{>elemId}}\" class=\"date-selector\">\n <select class=\"\" name=\"year\">\n {{for selectYear}}\n <option value=\"{{>year}}\"{{if selected}} selected=\"selected\"{{/if}}>{{>year}}</option>\n {{/for}}\n </select> \n <select class=\"\" name=\"month\">\n {{for selectMonth}}\n <option value=\"{{>month}}\"{{if selected}} selected=\"selected\"{{/if}}>{{>month}}</option>\n {{/for}}\n </select>\n <input type=\"number\" name=\"months\" value=\"{{>viewMonths}}\" size=\"2\" />\n <span>{{> regional.months }}</span>\n <input class=\"\" type=\"submit\" value=\"{{>regional.go}}\" />\n </form>\n </div>\n <div class=\"nav\">\n <span class=\"buttons\">\n <a href=\"#\" class=\"to-prev\">&#9664;</a><a href=\"#\" class=\"to-this-month\">{{>regional.thisMonth}}</a><a href=\"#\" class=\"to-next\">&#9654;</a>\n </span>\n &nbsp;\n {{if writable}}\n <select class=\"select-style\">\n {{for styleSelect}}\n <option{{if selected}} selected=\"selected\"{{/if}} style=\"background-color: {{>color}};\" value=\"{{>style}}\">{{>name}}</option>\n {{/for}}\n </select>\n {{/if}}\n </div>\n </div>\n <div class=\"chart\">\n <table>\n <tr>\n <td style=\"position:relative;\" class=\"subjects\">\n <table style=\"position:absolute; top:{{>tableTop}}px; left: 0px;\">\n <!--div style=\"position:regional; height: {{>tHeight + 1}}px; width: {{>subjectWidth + 1}}px;\"-->\n <thead>\n <tr>\n <th style=\"height: {{>lineHeight}}px;\" class=\"col-list\" colspan=\"5\">\n <select class=\"colmun-selecter\">\n <option></option>\n <option value=\"start-date\">{{>regional.startDate}}</option>\n <option value=\"due-date\">{{>regional.dueDate}}</option>\n <option value=\"owner\">{{>regional.owner}}</option>\n </select>\n </th>\n </tr>\n <tr>\n <th style=\"height: {{>lineHeight}}px;\" class=\"subject-index\" data-colname=\"subject-name\"> </th>\n <th style=\"height: {{>lineHeight}}px;\" class=\"subject-name\" data-colname=\"subject-name\"> </th>\n <th style=\"height: {{>lineHeight}}px;\" class=\"start-date hidden delete-btn\" data-colname=\"start-date\"> </th>\n <th style=\"height: {{>lineHeight}}px;\" class=\"due-date hidden delete-btn\" data-colname=\"due-date\"> </th>\n <th style=\"height: {{>lineHeight}}px;\" class=\"owner delete-btn\" data-colname=\"owner\"> </th>\n </tr>\n </thead>\n <tbody>\n {{for subjects tmpl=\"gantt-subjects\" /}}\n </tbody>\n </table>\n </td>\n <td>\n <div style=\"position:relative; height: {{>tHeight + 1}}px; overflow:auto;\" id=\"gantt_area\">\n <div style=\"width: {{>gWidth - 1}}px; height: {{>headersHeight}}px;\" class=\"gantt_hdr header\"> </div>\n {{!-- ###### Months headers ###### --}}\n {{for months}}\n <div style=\"left:{{>left}}px; width:{{>width}}px; height:{{>height}}px;\" class=\"gantt_hdr bottom\">\n {{>month}}\n </div>\n {{/for}}\n\n {{!-- ###### Days headers ###### --}}\n {{for days}}\n <div style=\"left:{{>left}}px; top:{{>top}}px; width:{{>width}}px; height:{{>height}}px;\" class=\"{{>class_}} bottom\">\n {{>day[0]}}\n </div>\n {{/for}}\n {{for days}}\n <div style=\"left:{{>left}}px; top:{{>top*2}}px; width:{{>width}}px; height:{{>height}}px;\" class=\"{{>class_}} bottom\">\n {{>day[1]}}\n </div>\n {{/for}}\n {{for days}}\n <div style=\"left:{{>left}}px; top:{{>top*3}}px; width:{{>width}}px; height:{{>gHeight}}px;\" class=\"{{>class_}}\">\n </div>\n {{/for}}\n {{for lines}}\n <div style=\"left:0px; top:{{>line_top}}px; height:{{>lineHeight}}px; width: {{>gWidth}}px;\" class=\"gantt_line task-line\" data-gantt-idx=\"{{>no}}\">\n {{include tmpl=\"gantt-popup\" /}}\n </div>\n {{/for}}\n\n {{!-- ###### Today's line ##### --}}\n {{if today}}\n <div style=\"position:absolute; height:{{>gHeight + 1}}px; top:{{>headersHeight-1}}px; left:{{>today.todayLeft}}px; width:10px;\" class=\"gantt_today\">\n </div>\n {{/if}}\n\n <div id=\"gantt_draw_area\" style=\"position:absolute; height:{{>gHeight}}px; top:{{>headersHeight + 1}}px; left:0px; width:{{>gWidth - 1}}px;\">\n {{for lines tmpl=\"gantt-lines\" /}}\n </div>\n </div>\n </td>\n </tr>\n </table>\n </div>\n</div>");
