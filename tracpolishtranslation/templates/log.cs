<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <ul>
  <li class="last"><a href="<?cs
    var:log.browser_href ?>">Przegl�d ostatniej rewizji</a></li><?cs
  if:len(chrome.links.prev) ?>
   <li class="first<?cs if:!len(chrome.links.next) ?> last<?cs /if ?>">
    &larr; <a href="<?cs var:chrome.links.prev.0.href ?>" title="<?cs
      var:chrome.links.prev.0.title ?>">Nowsza rewizja</a>
   </li><?cs
  /if ?><?cs
  if:len(chrome.links.next) ?>
   <li class="<?cs if:!len(chrome.links.prev) ?>first <?cs /if ?>last">
    <a href="<?cs var:chrome.links.next.0.href ?>" title="<?cs
      var:chrome.links.next.0.title ?>">Starsza rewizja</a> &rarr;
   </li><?cs
  /if ?>
 </ul>
</div>


<div id="content" class="log">
 <h1><?cs call:browser_path_links(log.path, log) ?></h1>
 <form id="prefs" action="<?cs var:browser_current_href ?>" method="get">
  <div>
   <input type="hidden" name="action" value="<?cs var:log.mode ?>" />
   <label>View log starting at <input type="text" id="rev" name="rev" value="<?cs
    var:log.items.0.rev ?>" size="5" /></label>
   <label>and back to <input type="text" id="stop_rev" name="stop_rev" value="<?cs
    var:log.stop_rev ?>" size="5" /></label>
   <br />
   <div class="choice">
    <fieldset>
     <legend>Mode:</legend>
     <label for="stop_on_copy">
      <input type="radio" id="stop_on_copy" name="mode" value="stop_on_copy" <?cs
       if:log.mode != "follow_copy" || log.mode != "path_history" ?> checked="checked" <?cs
       /if ?> />
      Zatrzymaj si� na kopii 
     </label>
     <label for="follow_copy">
      <input type="radio" id="follow_copy" name="mode" value="follow_copy" <?cs
       if:log.mode == "follow_copy" ?> checked="checked" <?cs /if ?> />
      Przechod� przez kopie
     </label>
     <label for="path_history">
      <input type="radio" id="path_history" name="mode" value="path_history" <?cs
       if:log.mode == "path_history" ?> checked="checked" <?cs /if ?> />
      Pokazuj tylko pliki dodane, przeniesione i usuni�te
     </label>
    </fieldset>
   </div>
   <label><input type="checkbox" name="verbose" <?cs
    if:log.verbose ?> checked="checked" <?cs
    /if ?> /> Pokazuj szczeg�owe logi</label>
  </div>
  <div class="buttons">
   <input type="submit" value="Update" 
          title="Ostrzerzenie: po zaktualizowaniu, historia strony zostanie wymazana" />
  </div>
 </form>
 <div class="diff">
  <div id="legend">
   <h3>Legend:</h3>
   <dl>
    <dt class="add"></dt><dd>Dodane</dd><?cs
    if:log.mode == "path_history" ?>
     <dt class="rem"></dt><dd>Usuni�te</dd><?cs
    /if ?>
    <dt class="mod"></dt><dd>Modyfikowane</dd>
    <dt class="cp"></dt><dd>Skopiowane lub ze zmienion� nazw�</dd>
   </dl>
  </div>
 </div>
 <table id="chglist" class="listing">
  <thead>
   <tr>
    <th class="change"></th>
    <th class="data">Data</th>
    <th class="rev">Rew</th>
    <th class="chgset">Zmiana</th>
    <th class="author">Autor</th>
    <th class="summary">Logi</th>
   </tr>
  </thead>
  <tbody><?cs
   set:indent = #1 ?><?cs
   each:item = log.items ?><?cs
    if:item.copyfrom_path ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="copyfrom_path" colspan="6" style="padding-left: <?cs var:indent ?>em">
       copied from <a href="<?cs var:item.browser_href ?>"?><?cs var:item.copyfrom_path ?></a>:
      </td>
     </tr><?cs
     set:indent = indent + #1 ?><?cs
    elif:log.mode == "path_history" ?><?cs
      set:indent = #1 ?><?cs
    /if ?>
    <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
     <td class="change" style="padding-left:<?cs var:indent ?>em">
      <a title="View log starting at this revision" href="<?cs var:item.log_href ?>">
       <span class="<?cs var:item.change ?>"></span>
       <span class="comment">(<?cs var:item.change ?>)</span>
      </a>
     </td>
     <td class="date"><?cs var:log.changes[item.rev].date ?></td>
     <td class="rev">
      <a href="<?cs var:item.browser_href ?>" 
         title="Browse at revision <?cs var:item.rev ?>">@<?cs var:item.rev ?></a>
     </td>
     <td class="chgset">
      <a href="<?cs var:item.changeset_href ?>"
         title="View changeset [<?cs var:item.rev ?>]">[<?cs var:item.rev ?>]</a>
     </td>
     <td class="author"><?cs var:log.changes[item.rev].author ?></td>
     <td class="summary"><?cs var:log.changes[item.rev].message ?></td>
    </tr><?cs
   /each ?>
  </tbody>
 </table><?cs
 if:len(links.prev) || len(links.next) ?><div id="paging" class="nav"><ul><?cs
  if:len(links.prev) ?><li class="first<?cs
   if:!len(links.next) ?> last<?cs /if ?>">&larr; <a href="<?cs
   var:links.prev.0.href ?>" title="<?cs
   var:links.prev.0.title ?>">Wcze�niejsze rewizje</a></li><?cs
  /if ?><?cs
  if:len(links.next) ?><li class="<?cs
   if:len(links.prev) ?>first <?cs /if ?>last"><a href="<?cs
   var:links.next.0.href ?>" title="<?cs
   var:links.next.0.title ?>">Starsze rewizje</a> &rarr;</li><?cs
  /if ?></ul></div><?cs
 /if ?>

</div>
<?cs include "footer.cs"?>
