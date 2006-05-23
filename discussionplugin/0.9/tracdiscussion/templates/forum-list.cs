<?cs include "discussion-header.cs" ?>

<h1>Forum Index</h1>
<table class="listing">
  <thead>
    <tr>
      <th class="subject">Forum</th>
      <th class="moderators">Moderators</th>
      <th class="lastreply">Last Reply</th>
      <th class="founded">Founded</th>
      <th class="topics">Topics</th>
      <th class="replies">Replies</th>
    </tr>
  </thead>
  <tbody>
    <?cs each:forum = discussion.forums ?>
      <tr class="<?cs if:name(forum) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
        <td class="subject">
          <a class="cell" href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
            <div class="subject">
              <?cs var:forum.subject ?>
            </div>
            <div class="description">
              <?cs var:forum.description ?>
            </div>
          </a>
        </td>
        <td class="moderators">
          <a class="cell" href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
            <div class="moderators">
              <?cs var:forum.moderators ?>
            </div>
          </a>
        </td>
        <td class="lastreply">
          <a class="cell" href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
            <div class="lastreply">
              Not implemented
            </div>
          </a>
        </td>
        <td class="founded">
          <a class="cell" href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
            <div class="founded">
              <?cs var:forum.time ?>
            </div>
          </a>
        </td>
        <td class="topics">
          <a class="cell" href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
            <div class="topics">
              <?cs var:forum.topics ?>
            </div>
          </a>
        </td>
        <td class="replies">
          <a class="cell" href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
            <div class="replies">
              <?cs var:forum.replies ?>
            </div>
          </a>
        </td>
      </tr>
    <?cs /each ?>
  </tbody>
</table>

<?cs if:trac.acl.DISCUSSION_MODIFY ?>
  <form method="post" action="<?cs var:trac.href.discussion ?>">
    <div class="buttons">
      <input type="submit" name="newforum" value="New Forum"/>
    </div>
    <input type="hidden" name="action" value="add"/>
  </form>
<?cs /if ?>

<?cs include "discussion-footer.cs" ?>
