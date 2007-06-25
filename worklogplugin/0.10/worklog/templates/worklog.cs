<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<form method="post" action="<?cs var:worklog.href ?>" >
<div id="content" class="worklog">
  <a id="worklogmanual" href="<?cs var:worklog.usermanual_href ?>" ><?cs var:worklog.usermanual_title ?></a>
  <div id="messages" >
    <?cs each:item = worklog.messages ?>
      <div class="message" ><?cs var:item ?></div>
    <?cs /each ?>
  </div>

  <table border="0" cellspacing="0" cellpadding="0">
    <tr>
      <th>User</th>
      <th>Activity</th>
      <th>Last Change</th>
    </tr>
    <?cs each:log = worklog.worklog ?>
    <tr>
      <td><?cs var:log.name ?> (<?cs var:log.user ?>)</td>
      <?cs if:log.started_at > #0 ?>
      <?cs if:log.state == #1 ?>
      <td><a href="<?cs var:log.ticket_url ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?></td>
      <?cs else ?>
      <td><em>Idle</em> <small>(Last worked on: <a href="<?cs var:log.ticket_url ?>">#<?cs var:log.ticket ?></a>: <?cs var:log.summary ?>)</small></td>      
      <?cs /if ?>
      <td><?cs var:log.started_at_human ?></td>
      <?cs else ?>
      <td colspan="2"><em><?cs var:log.name ?> has never done an iota of work.... EVER!!</em></td>
      <?cs /if ?>
    </tr>
    <?cs /each ?>
  </table>
</div>
</form>
<?cs include "footer.cs"?>