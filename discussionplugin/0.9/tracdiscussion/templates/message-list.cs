<?cs include "discussion-header.cs" ?>

<?cs def:display_preview() ?>
  <li class="preview">
    <a name="preview"></a>
    <div class="body">
      <?cs var:discussion.body ?>
    </div>
    <div class="author">
      <?cs var:discussion.author ?>
    </div>
  </li>
<?cs /def ?>

<?cs def:display_form() ?>
  <li class="reply">
    <fieldset>
      <a name="reply"></a>
      <legend>
         Reply:
      </legend>
      <form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>#preview">
        <div class="field">
          <label for="author">Author:</label><br/>
          <?cs if:args.author ?>
            <input type="text" name="author" value="<?cs var:args.author ?>"/><br/>
          <?cs else ?>
            <input type="text" name="author" value="<?cs var:discussion.authname ?>"/><br/>
          <?cs /if ?>
        </div>
        <div class="field">
          <label for="body">Body:</label><br/>
          <textarea name="body" class="wikitext" rows="10" cols="78"><?cs alt:args.body ?>Enter your message here...<?cs /alt ?></textarea>
        </div>
        <div class="buttons">
          <input type="submit" name="preview" value="Preview"/>
          <input type="submit" name="submit" value="Reply"/>
          <input type="button" name="cancel" value="Cancel" onClick="location.href = '<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>'"/>
        </div>
        <input type="hidden" name="reply" value="<?cs var:args.reply ?>"/>
        <input type="hidden" name="action" value="post-add"/>
      </form>
    </fieldset>
  </li>
<?cs /def ?>

<?cs def:display_topic(messages) ?>
  <?cs each:message = messages ?>
    <li>
      <a name="<?cs var:message.id ?>"></a>
      <div class="body">
        <?cs var:message.body ?>
      </div>
      <div class="controls">
        <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>?action=add;reply=<?cs var:message.id ?>#reply">Reply</a>
        <?cs if:trac.acl.DISCUSSION_MODERATE && discussion.is_moderator ?>
          <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>?action=delete;reply=<?cs var:message.id ?>" onClick="return confirm('Do you realy want to delete this reply and all its descendants?')"/>Delete</a>
        <?cs /if ?>
      </div>
      <div class="author">
        <?cs var:message.author ?>
      </div>
    </li>
    <?cs if:discussion.messages.0.body || (args.action == "add") || (args.action == "post-add") ?>
      <ul>
        <?cs call:display_topic(message.replies) ?>
        <?cs if:args.preview && args.reply == message.id ?>
           <?cs call:display_preview() ?>
        <?cs /if ?>
        <?cs if:!args.submit && args.reply == message.id ?>
          <?cs call:display_form() ?>
        <?cs /if ?>
      </ul>
    <?cs /if ?>
  <?cs /each ?>
<?cs /def ?>

<h1 class="forum-subject"><?cs var:discussion.forum.subject ?> - Message List</h1>
<a name="-1"></a>
<div class="topic">
  <div class="header">
    <div class="subject">
      <?cs var:discussion.topic.subject ?>
    </div>
    <div class="body">
      <?cs var:discussion.topic.body ?>
    </div>
    <div class="controls">
      <a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>?action=add;reply=-1#reply">Reply</a>
    </div>
    <div class="author">
      <?cs var:discussion.topic.author ?>
    </div>
  </div>
  <?cs if:discussion.messages.0.body || (args.action == "add") || (args.action == "post-add") ?>
    <div class="replies">
      <ul>
        <?cs call:display_topic(discussion.messages) ?>
        <?cs if:args.preview && args.reply == -1 ?>
           <?cs call:display_preview() ?>
        <?cs /if ?>
        <?cs if:!args.submit && args.reply == -1 ?>
          <?cs call:display_form() ?>
        <?cs /if ?>
      </ul>
    </div>
  <?cs /if ?>
</div>

<?cs if:trac.acl.DISCUSSION_MODERATE && discussion.is_moderator ?>
  <div class="buttons">
    <form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.id ?>/<?cs var:discussion.topic.id ?>">
      <input type="submit" name="deletetopic" value="Delete Topic" onClick="return confirm('Do you realy want to delete this topic?')"/>
      <input type="hidden" name="action" value="delete"/>
      <input type="hidden" name="reply" value="-1">
    </form>
  </div>
<?cs /if ?>

<?cs include "discussion-footer.cs" ?>
