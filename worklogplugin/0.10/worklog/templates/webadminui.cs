<h2>Work Log Settings</h2>

<form method="post">
  <fieldset>
    <legend>Options:</legend>
    <p style="font-weight: bold">
      NONE of these options currently work as intended and they should all be disabled.<br>
      If they are enabled they will change how things operate in which will break several logical things and leave you
      with a potentially very confused database.<br>
      Implementations will come in time, please be patient!
    </p>
    <div class="field">
      <input type="checkbox" id="timingandestimation" name="timingandestimation" value="1" <?cs var:settings.timingandestimation ?>>
      <label for="timingandestimation">Record time via <a href="http://www.trac-hacks.org/wiki/TimingAndEstimationPlugin">Timing and Estimation Plugin</a>?</label>
    </div>
    <div class="field">
      <input type="checkbox" id="comment" name="comment" value="1" <?cs var:settings.comment ?>>
      <label for="comment">Automatically add a comment when you stop work on a ticket?</label>
    </div>
    <div class="field">
      <input type="checkbox" id="autostop" name="autostop" value="1" <?cs var:settings.autostop ?>>
      <label for="autostop">Stop work automatically if ticket is closed?</label>
    </div>
    <div class="field">
      <input type="checkbox" id="autoreassignaccept" name="autoreassignaccept" value="1" <?cs var:settings.autoreassignaccept ?>>
      <label for="autoreassignaccept">Automatically reassign and accept (if necessary) when starting work?</label>
    </div>
    <div class="field">
      <input type="checkbox" id="autostopstart" name="autostopstart" value="1" <?cs var:settings.autostop ?>>
      <label for="autostopstart">Allow users to start working on a different ticket (i.e. automatically stop working on current ticket)?</label>
    </div>
  </fieldset>
  <br>
  <fieldset>
    <legend>Paramaters:</legend>
    <div class="field">
      <label for="roundup">Round up to nearest minute</label>&nbsp;
      <input type="text" id="roundup" name="roundup" size="4" value="<?cs var:settings.roundup ?>"><br>
      <small>This only applies when integrating with the 
             <a href="http://www.trac-hacks.org/wiki/TimingAndEstimationPlugin">Timing and Estimation Plugin</a></small>
    </div>
  </fieldset>

  <div class="buttons">
    <input type="submit" name="update" value="Update Settings" />
  </div>
</form>
