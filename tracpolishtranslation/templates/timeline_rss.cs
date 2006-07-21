<?xml version="1.0"?>
<rss version="2.0">
 <channel><?cs
  if:project.name_encoded ?>
   <title><?cs var:project.name_encoded ?>: <?cs var:title ?></title><?cs
  else ?>
   <title><?cs var:title ?></title><?cs
  /if ?>
  <link><?cs var:base_host ?><?cs var:trac.href.timeline ?></link>
  <description>Trac Timeline</description>
  <language>pl-PL</language>
  <generator>Trac v<?cs var:trac.version ?></generator><?cs
  if:chrome.logo.src ?>
   <image>
    <title><?cs var:project.name_encoded ?></title>
    <url><?cs if:!chrome.logo.src_abs ?><?cs var:base_host ?><?cs /if ?><?cs
     var:chrome.logo.src ?></url>
    <link><?cs var:base_host ?><?cs var:trac.href.timeline ?></link>
   </image><?cs
  /if ?><?cs
  each:event = timeline.events ?>
   <item>
    <title><?cs var:event.title ?></title><?cs
    if:event.author.email ?>
     <author><?cs var:event.author.email ?></author><?cs
    /if ?>
    <pubDate><?cs var:event.date ?></pubDate>
    <link><?cs var:event.href ?></link>
    <description><?cs var:event.message ?></description>
   </item><?cs
  /each ?>
 </channel>
</rss>
