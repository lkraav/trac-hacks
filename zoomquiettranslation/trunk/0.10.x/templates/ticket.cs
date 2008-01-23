<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
 <h2>Ticket Navigation</h2><?cs
 with:links = chrome.links ?><?cs
  if:len(links.prev) || len(links.up) || len(links.next) ?><ul><?cs
   if:len(links.prev) ?>
    <li class="first<?cs if:!len(links.up) && !len(links.next) ?> last<?cs /if ?>">
     &larr; <a href="<?cs var:links.prev.0.href ?>" title="<?cs
       var:links.prev.0.title ?>">上一条传票</a>
    </li><?cs
   /if ?><?cs
   if:len(links.up) ?>
    <li class="<?cs if:!len(links.prev) ?>first<?cs /if ?><?cs
                    if:!len(links.next) ?> last<?cs /if ?>">
     <a href="<?cs var:links.up.0.href ?>" title="<?cs
       var:links.up.0.title ?>">自定义查询</a>
    </li><?cs
   /if ?><?cs
   if:len(links.next) ?>
    <li class="<?cs if:!len(links.prev) && !len(links.up) ?>first <?cs /if ?>last">
     <a href="<?cs var:links.next.0.href ?>" title="<?cs
       var:links.next.0.title ?>">下一条传票</a> &rarr;
    </li><?cs
   /if ?></ul><?cs
  /if ?><?cs
 /with ?>
</div>

<div id="content" class="ticket">

 <h1>Ticket #<?cs var:ticket.id ?> <span class="status">(<?cs 
  var:ticket.status ?><?cs 
  if:ticket.type ?> <?cs var:ticket.type ?><?cs 
  /if ?><?cs 
  if:ticket.resolution ?>: <?cs var:ticket.resolution ?><?cs 
  /if ?>)</span></h1>

<div id="searchable">
<div id="ticket">
 <div class="date">
  <p title="<?cs var:ticket.opened ?>">创建时间 <?cs var:ticket.opened_delta ?> 前</p><?cs
  if:ticket.lastmod ?>
   <p title="<?cs var:ticket.lastmod ?>">更新时间 <?cs var:ticket.lastmod_delta ?> 前</p>
  <?cs /if ?>
 </div>
 <h2 class="summary"><?cs var:ticket.summary ?></h2>
 <table class="properties">
  <tr>
   <th id="h_reporter">创建:</th>
   <td headers="h_reporter"><?cs var:ticket.reporter ?></td>
   <th id="h_owner">指派到:</th>
   <td headers="h_owner"><?cs var:ticket.owner ?><?cs
     if:ticket.status == 'assigned' ?> (接受)<?cs /if ?></td>
  </tr><tr><?cs
  each:field = ticket.fields ?><?cs
   if:!field.skip ?><?cs
    set:num_fields = num_fields + 1 ?><?cs
   /if ?><?cs
  /each ?><?cs
  set:idx = 0 ?><?cs
  each:field = ticket.fields ?><?cs
   if:!field.skip ?><?cs set:fullrow = field.type == 'textarea' ?><?cs
    if:fullrow && idx % 2 ?><th></th><td></td></tr><tr><?cs /if ?>
    <th id="h_<?cs var:name(field) ?>"><?cs var:field.label ?>:</th>
    <td<?cs if:fullrow ?> colspan="3"<?cs /if ?> headers="h_<?cs
      var:name(field) ?>"><?cs var:ticket[name(field)] ?></td><?cs 
    if:idx % 2 || fullrow ?></tr><tr><?cs 
    elif:idx == num_fields - 1 ?><th></th><td></td><?cs
    /if ?><?cs set:idx = idx + #fullrow + 1 ?><?cs
   /if ?><?cs
  /each ?></tr>
 </table><?cs 
 if:ticket.description ?>
  <form method="get" action="<?cs var:ticket.href ?>#comment" class="printableform">
   <div class="description">
    <h3 id="comment:description"><?cs
     if:trac.acl.TICKET_APPEND ?>
     <span class="inlinebuttons">
      <input type="hidden" name="replyto" value="description" />
      <input type="submit" value="回复" title="Reply, quoting this description" />
     </span><?cs
     /if ?>
     描述<?cs
     if:ticket.description.lastmod ?><span class="lastmod" title="<?cs var:ticket.description.lastmod ?>">(Last modified by <?cs var:ticket.description.author ?>)</span><?cs
     /if ?>
    </h3>
    <?cs var:ticket.description.formatted ?>
   </div>
  </form><?cs 
 /if ?>
</div>

<?cs if:ticket.attach_href || len(ticket.attachments) ?>
<?cs call:list_of_attachments(ticket.attachments, ticket.attach_href) ?>
<?cs /if ?>

<?cs def:commentref(prefix, cnum) ?>
<a href="#comment:<?cs var:cnum ?>"><small><?cs var:prefix ?><?cs var:cnum ?></small></a>
<?cs /def ?>

<?cs if:len(ticket.changes) ?><h2>修改历史</h2>
<div id="changelog"><?cs
 each:change = ticket.changes ?>
 <form method="get" action="<?cs var:ticket.href ?>#comment" class="printableform">
 <div class="change">
  <h3 <?cs if:change.cnum ?>id="comment:<?cs var:change.cnum ?>"<?cs /if ?>><?cs
   if:change.cnum ?><?cs
    if:trac.acl.TICKET_APPEND ?>
    <span class="inlinebuttons">
     <input type="hidden" name="replyto" value="<?cs var:change.cnum ?>" />
     <input type="submit" value="回复" title="Reply to comment <?cs var:change.cnum ?>" />
    </span><?cs
    /if ?>
    <span class="threading"><?cs
     set:nreplies = len(ticket.replies[change.cnum]) ?><?cs
     if:nreplies || change.replyto ?>(<?cs
      if:change.replyto ?>上条回复: <?cs 
       call:commentref('&uarr;&nbsp;', change.replyto) ?><?cs if nreplies ?>; <?cs /if ?><?cs
      /if ?><?cs
      if nreplies ?><?cs
       call:plural('下条回复', nreplies) ?>: <?cs 
       each:reply = ticket.replies[change.cnum] ?><?cs 
        call:commentref('&darr;&nbsp;', reply) ?><?cs 
       /each ?><?cs 
      /if ?>)<?cs
    /if ?>
    </span><?cs
   /if ?><?cs
   var:change.date ?> 编辑者 <?cs var:change.author ?>
  </h3><?cs
  if:len(change.fields) ?>
   <ul class="changes"><?cs
   each:field = change.fields ?>
    <li><strong><?cs var:name(field) ?></strong> <?cs
    if:name(field) == 'attachment' ?><em><?cs var:field.new ?></em>增加<?cs
    elif:field.old && field.new ?>从 <em><?cs
     var:field.old ?></em> 修改为 <em><?cs var:field.new ?></em><?cs
    elif:!field.old && field.new ?>设置为 <em><?cs var:field.new ?></em><?cs
    elif:field.old && !field.new ?>删除<?cs
    else ?>修改<?cs
    /if ?>.</li>
    <?cs
   /each ?>
   </ul><?cs
  /if ?>
  <div class="comment"><?cs var:change.comment ?></div>
 </div>
 </form><?cs
 /each ?>
</div><?cs
/if ?>

<?cs if:trac.acl.TICKET_CHGPROP || trac.acl.TICKET_APPEND ?>
<form action="<?cs var:ticket.href ?>#preview" method="post">
 <hr />
 <h3><a name="edit" onfocus="document.getElementById('comment').focus()">添加/修改 #<?cs
   var:ticket.id ?> (<?cs var:ticket.summary ?>)</a></h3>
 <?cs if:trac.authname == "anonymous" ?>
  <div class="field">
   <label for="author">输入用户名或者信箱地址:</label><br />
   <input type="text" id="author" name="author" size="40"
     value="<?cs var:ticket.reporter_id ?>" /><br />
  </div>
 <?cs /if ?>
 <div class="field">
  <fieldset class="iefix">
   <label for="comment">评论 (<a tabindex="42" href="<?cs
     var:trac.href.wiki ?>/ZhWikiFormatting">维基格式说明</a>帮助):</label><br />
   <p><textarea id="comment" name="comment" class="wikitext" rows="10" cols="78">
<?cs var:ticket.comment ?></textarea></p>
  </fieldset><?cs
  if ticket.comment_preview ?>
   <fieldset id="preview">
    <legend>评论 预览</legend>
    <?cs var:ticket.comment_preview ?>
   </fieldset><?cs
  /if ?>
 </div>

 <?cs if:trac.acl.TICKET_CHGPROP ?><fieldset id="properties">
  <legend>修改属性</legend>
  <table><tr>
   <th><label for="summary">描述:</label></th>
   <td class="fullrow" colspan="3"><input type="text" id="summary" name="summary" value="<?cs
     var:ticket.summary ?>" size="70" /></td>
   </tr><?cs
   if:len(ticket.fields.type.options) ?>
   <tr>
    <th><label for="type">类型:</label></th>
    <td><?cs 
     call:hdf_select(ticket.fields.type.options, 'type', ticket.type, 0) ?>
    </td>
   </tr><?cs
   /if ?><?cs
   if:trac.acl.TICKET_ADMIN ?><tr>
    <th><label for="description">详细描述:</label></th>
    <td class="fullrow" colspan="3">
     <textarea id="description" name="description" class="wikitext" rows="10" cols="68">
<?cs var:ticket.description ?></textarea>
    </td>
   </tr><tr>
    <th><label for="reporter">报表人:</label></th>
    <td class="fullrow" colspan="3"><input type="text" value="<?cs 
      var:ticket.reporter ?>" id="reporter" name="reporter" size="70" /></td>
   </tr><?cs
   /if ?>
  <tr><?cs set:num_fields = 0 ?><?cs
  each:field = ticket.fields ?><?cs
   if:!field.skip ?><?cs
    set:num_fields = num_fields + 1 ?><?cs
   /if ?><?cs
  /each ?><?cs set:idx = 0 ?><?cs
   each:field = ticket.fields ?><?cs
    if:!field.skip ?><?cs set:fullrow = field.type == 'textarea' ?><?cs
     if:fullrow && idx % 2 ?><?cs set:idx = idx + 1 ?><th class="col2"></th><td></td></tr><tr><?cs /if ?>
     <th class="col<?cs var:idx % 2 + 1 ?>"><?cs
       if:field.type != 'radio' ?><label for="<?cs var:name(field) ?>"><?cs
       /if ?><?cs alt:field.label ?><?cs var:field.name ?><?cs /alt ?>:<?cs
       if:field.type != 'radio' ?></label><?cs /if ?></th>
     <td<?cs if:fullrow ?> colspan="3"<?cs /if ?>><?cs
      if:field.type == 'text' ?><input type="text" id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" value="<?cs var:ticket[name(field)] ?>" /><?cs
      elif:field.type == 'select' ?><select id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>"><?cs
        if:field.optional ?><option></option><?cs /if ?><?cs
        each:option = field.options ?><option<?cs
         if:option == ticket[name(field)] ?> selected="selected"<?cs /if ?>><?cs
         var:option ?></option><?cs
        /each ?></select><?cs
      elif:field.type == 'checkbox' ?><input type="hidden" name="checkbox_<?cs
        var:name(field) ?>" /><input type="checkbox" id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" value="1"<?cs
        if:ticket[name(field)] ?> checked="checked"<?cs /if ?> /><?cs
      elif:field.type == 'textarea' ?><textarea id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>"<?cs
        if:field.height ?> rows="<?cs var:field.height ?>"<?cs /if ?><?cs
        if:field.width ?> cols="<?cs var:field.width ?>"<?cs /if ?>>
<?cs var:ticket[name(field)] ?></textarea><?cs
      elif:field.type == 'radio' ?><?cs set:optidx = 0 ?><?cs
       each:option = field.options ?><label><input type="radio" id="<?cs
         var:name(field) ?>" name="<?cs
         var:name(field) ?>" value="<?cs var:option ?>"<?cs
         if:ticket[name(field)] == option ?> checked="checked"<?cs /if ?> /> <?cs
         var:option ?></label> <?cs set:optidx = optidx + 1 ?><?cs
        /each ?><?cs
      /if ?></td><?cs
     if:idx % 2 || fullrow ?><?cs
      if:idx < num_fields - 1 ?></tr><tr><?cs
      /if ?><?cs 
     elif:idx == num_fields - 1 ?><th class="col2"></th><td></td><?cs
     /if ?><?cs set:idx = idx + #fullrow + 1 ?><?cs
    /if ?><?cs
   /each ?></tr>
  </table>
 </fieldset><?cs /if ?>

 <?cs if:ticket.actions.accept || ticket.actions.reopen ||
         ticket.actions.resolve || ticket.actions.reassign ?>
 <fieldset id="action">
  <legend>操作</legend><?cs
  if:!ticket.action ?><?cs set:ticket.action = 'leave' ?><?cs
  /if ?><?cs
  def:action_radio(id) ?>
   <input type="radio" id="<?cs var:id ?>" name="action" value="<?cs
     var:id ?>"<?cs if:ticket.action == id ?> checked="checked"<?cs
     /if ?> /><?cs
  /def ?>
  <?cs call:action_radio('leave') ?>
   <label for="leave">状态保持为: <?cs var:ticket.status ?></label><br /><?cs
  if:ticket.actions.accept ?><?cs
   call:action_radio('accept') ?>
   <label for="accept">接受传票</label><br /><?cs
  /if ?><?cs
  if:ticket.actions.reopen ?><?cs
   call:action_radio('reopen') ?>
   <label for="reopen">重开传票</label><br /><?cs
  /if ?><?cs
  if:ticket.actions.resolve ?><?cs
   call:action_radio('resolve') ?>
   <label for="resolve">处理为:</label><?cs
   if:len(ticket.fields.resolution.options) ?>
    <label for="resolve_resolution"></label>
    <?cs call:hdf_select(ticket.fields.resolution.options, "resolve_resolution",
                         ticket.resolve_resolution, 0) ?><br /><?cs
   /if ?><?cs
  /if ?><?cs
  if:ticket.actions.reassign ?><?cs
   call:action_radio('reassign') ?>
   <label for="reassign">重指派到:</label>
   <label><?cs
   if:len(ticket.fields.owner.options) ?><?cs
    call:hdf_select(ticket.fields.owner.options, "reassign_owner",
                    ticket.reassign_owner, 1) ?><?cs
   else ?>
    <input type="text" id="reassign_owner" name="reassign_owner" size="40" value="<?cs
      var:ticket.reassign_owner ?>" /><?cs
   /if ?></label><?cs
  /if ?><?cs
  if ticket.actions.resolve || ticket.actions.reassign ?>
   <script type="text/javascript"><?cs
    each:action = ticket.actions ?>
     var <?cs var:name(action) ?> = document.getElementById("<?cs var:name(action) ?>");<?cs
    /each ?>
     var updateActionFields = function() {
       <?cs if:ticket.actions.resolve ?> enableControl('resolve_resolution', resolve.checked);<?cs /if ?>
       <?cs if:ticket.actions.reassign ?> enableControl('reassign_owner', reassign.checked);<?cs /if ?>
     };
     addEvent(window, 'load', updateActionFields);<?cs
     each:action = ticket.actions ?>
      addEvent(<?cs var:name(action) ?>, 'click', updateActionFields);<?cs
     /each ?>
   </script><?cs
  /if ?>
 </fieldset><?cs
 else ?>
  <input type="hidden" name="action" value="leave" /><?cs
 /if ?>

 <script type="text/javascript" src="<?cs
   var:htdocs_location ?>js/wikitoolbar.js"></script>

 <div class="buttons">
  <input type="hidden" name="ts" value="<?cs var:ticket.ts ?>" />
  <input type="hidden" name="replyto" value="<?cs var:ticket.replyto ?>" />
  <input type="hidden" name="cnum" value="<?cs var:ticket.cnum ?>" />
  <input type="submit" name="preview" value="预览 " accesskey="r" />&nbsp;
  <input type="submit" value="提交" />
 </div>
</form>
<?cs /if ?>

 </div>
 <script type="text/javascript">
  addHeadingLinks(document.getElementById("searchable"), "Permalink to $id");
 </script>
</div>
<?cs include "footer.cs"?>
