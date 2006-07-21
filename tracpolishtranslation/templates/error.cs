<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="error">

 <?cs if error.type == "TracError" ?>
  <h3><?cs var:error.title ?></h3>
  <p class="message">
  <?cs var:error.message ?>
  </p>

 <?cs elif error.type == "internal" ?>
  <h3>Uups...</h3>
  <div class="message">
   <strong>Trac wykry� wewn�trzny b��d:</strong>
   <pre><?cs var:error.message ?></pre>
  </div>
  <p>
   Je�li uwa�asz, �e naprawd� powninno to dzia�a� i nie ma w tym Twojej winy. Mo�e powiniene� rozwa�y� raport tego problemu do Trac team.
  </p>
  <p>
   Id� do <a href="<?cs var:trac.href.homepage ?>"><?cs
     var:trac.href.homepage ?></a>  i stw�rz new ticket gdzie opiszesz problem i spos�b w jaki go otrzymujesz. Nie zapomnij do��czy� python traceback, kt�ry pojawi si� poni�ej.
  </p>

 <?cs elif error.type == "permission" ?>
  <h3>Brak dost�pu</h3>
  <p class="message">
  <?cs var:error.message ?>
  </p>
  <div id="help">
   <strong>Pomoc</strong>: Zobacz
   <a href="<?cs var:trac.href.wiki ?>/TracPermissions">TracPermissions</a>, aby dowiedzie� si� wi�cej o zabezpieczeniach.
  </div>

 <?cs /if ?>

 <p>
  <a href="<?cs var:trac.href.wiki ?>/TracGuide">TracGuide</a>
  &mdash; The Trac User and Administration Guide
 </p>

 <?cs if $error.traceback ?>
  <h4>Python traceback</h4>
  <pre><?cs var:error.traceback ?></pre>
 <?cs /if ?>

</div>
<?cs include "footer.cs"?>
