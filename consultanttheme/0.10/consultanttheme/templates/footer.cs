<script type="text/javascript">searchHighlight()</script><?cs
if:len(chrome.links.alternate) ?>
<div id="altlinks"><h3>Download in other formats:</h3><ul><?cs
 each:link = chrome.links.alternate ?><?cs
  set:isfirst = name(link) == 0 ?><?cs
  set:islast = name(link) == len(chrome.links.alternate) - 1?><li<?cs
    if:isfirst || islast ?> class="<?cs
     if:isfirst ?>first<?cs /if ?><?cs
     if:isfirst && islast ?> <?cs /if ?><?cs
     if:islast ?>last<?cs /if ?>"<?cs
    /if ?>><a href="<?cs var:link.href ?>"<?cs if:link.class ?> class="<?cs
    var:link.class ?>"<?cs /if ?>><?cs var:link.title ?></a></li><?cs
 /each ?></ul></div><?cs
/if ?>

</div>

<!--
<div id="footer">
 <hr />
 <a id="tracpowered" href="http://trac.edgewall.org/"><img src="<?cs
   var:htdocs_location ?>trac_logo_mini.png" height="30" width="107"
   alt="Trac Powered"/></a>
 <p class="left">
  Powered by <a href="<?cs var:trac.href.about ?>"><strong>Trac <?cs
  var:trac.version ?></strong></a><br />
  By <a href="http://www.edgewall.org/">Edgewall Software</a>.
 </p>
 <p class="right">
  <?cs var:project.footer ?>
 </p>
</div>
-->

<div id="footermainPan">
 <div id="footerPan">
  <div class="nav"><?cs call:nav(chrome.nav.mainnav, '', 0) ?></div>
  <p class="copyright">©gconsultant all right reaserved</p>
	
  <div id="footerPanhtml"><a href="http://validator.w3.org/check?uri=referer" target="_blank">html</a></div>
  <div id="footerPancss"><a href="http://jigsaw.w3.org/css-validator/check/referer" target="_blank">css</a></div>
  <div class="templateworld">Original Design By: <a href="http://www.templateworld.com" target="_blank">Template World</a></div>
</div>
</div>
<?cs include "site_footer.cs" ?>
 </body>
</html>
