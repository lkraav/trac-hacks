<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first<?cs if:!about.config_href ?> last<?cs /if ?>"><a href="<?cs
    var:trac.href.about ?>">概括</a></li><?cs
  if:about.config_href ?>
   <li><a href="<?cs var:about.config_href ?>">Configuration</a></li><?cs
  /if ?><?cs
  if:about.plugins_href ?>
   <li class="last"><a href="<?cs var:about.plugins_href ?>">Plugins</a></li><?cs
  /if ?>
 </ul>
</div>
<div id="content" class="about<?cs if:about.page ?>_<?cs var:about.page ?><?cs /if ?>">

 <?cs if:about.page == "config"?>
  <h1>Configuration</h1>
  <table><thead><tr><th class="section">Section</th>
   <th class="name">Name</th><th class="value">Value</th></tr></thead><?cs
  each:section = about.config ?><?cs
   if:len(section.options) ?>
    <tr><th class="section" rowspan="<?cs var:len(section.options) ?>"><?cs var:section.name ?></th><?cs
    each:option = section.options ?><?cs if:name(option) != 0 ?><tr><?cs /if ?>
     <td class="name"><?cs var:option.name ?></td>
     <td class="<?cs var:option.valueclass ?>"><?cs var:option.value ?></td>
    </tr><?cs
    /each ?><?cs
   /if ?><?cs
  /each ?></table>
  <div id="help">
   See <a href="<?cs var:trac.href.wiki ?>/TracIni">TracIni</a> for information about
   the configuration.
  </div>

 <?cs elif:about.page == "plugins" ?>
  <h1>Plugins</h1>
  <dl id="plugins"><?cs
   each:plugin = about.plugins ?>
    <h2 id="<?cs var:plugin.module ?>.<?cs var:plugin.name ?>"><?cs var:plugin.name ?></h2>
    <table>
     <tr>
      <th class="module" scope="row">Module</th>
      <td class="module"><?cs var:plugin.module ?><br />
      <span class="path"><?cs var:plugin.path ?></span></td>
     </tr><?cs
     if:plugin.description ?><tr>
      <th class="description" scope="row">Description</th>
      <td class="description"><?cs var:plugin.description ?></td>
     </tr><?cs /if ?><?cs
     if:len(plugin.extension_points) ?><tr>
      <th class="xtnpts" rowspan="<?cs var:len(plugin.extension_points) ?>">
       Extension points:</th><?cs
       each:extension_point = plugin.extension_points ?><?cs
        if:name(extension_point) != 0 ?><tr><?cs /if ?>
        <td class="xtnpts">        
         <code><?cs var:extension_point.module ?>.<?cs var:extension_point.interface ?></code><?cs
          if:len(extension_point.extensions) ?> (<?cs
           var:len(extension_point.extensions) ?> extensions)<ul><?cs
           each:extension = extension_point.extensions ?>
            <li><a href="#<?cs var:extension.module ?>.<?cs
              var:extension.name ?>"><?cs var:extension.name ?></a></li><?cs
           /each ?></ul><?cs
          /if ?>
          <div class="description"><?cs var:extension_point.description ?></div>
        </td></tr><?cs
       /each ?><?cs
     /if ?>
    </table><?cs
   /each ?>
  </dl>

 <?cs else ?>
  <a href="http://trac.edgewall.org/" style="border: none; float: right; margin-left: 2em">
   <img style="display: block" src="<?cs var:chrome.href ?>/common/trac_banner.png"
     alt="Trac: Integrated SCM &amp; Project Management"/>
  </a>
  <h1>关于Trac <?cs var:trac.version ?></h1>
  <p>Trac是一个以网络为基础的软件项目管理以及bug追踪系统。它重视的是使用的方便和低内存。
它提供了一个完整的Wiki、一个版本控制系统的界面以及很多方便地控制项目内的事件和更改的方法。
</p>
  <p>Trac是以更改的BSD许可证的形式分发的。许可证的文字内容可以在<a href="http://trac.edgewall.org/wiki/TracLicense">网上</a>找到，也可以在分发中包含的COPYING文件中找到。</p>
  <a href="http://www.python.org/" style="border: none; float: right">
   <img style="display: block" src="<?cs var:htdocs_location ?>python.png"
     alt="python powered" width="140" height="56" />
  </a>
  <p>访问Trac开源项目网站
  <a href="http://trac.edgewall.org/">http://trac.edgewall.org/</a>.</p>
  <p>Copyright &copy; 2003-2006 <a href="http://www.edgewall.org/">Edgewall
  Software</a></p>
 <?cs /if ?>
</div>
<?cs include "footer.cs"?>
