<h2>General Settings</h2>

<form class="mod" id="modhackinstallgeneral" method="post">
    <fieldset>
        <legend>Setting</legend>
        <div class="field">
            <label>URL:<br />
                <input type="text" name="url" value="<?cs var:hackinstall.url ?>" />
            </label>
        </div>
        <div class="field">
            <label>Version<br />
                <input type="text" name="version" id="version_field" value="<?cs var:hackinstall.version ?>" <?cs if:!hackinstall.override_version ?>disabled="true"<?cs /if ?>/><br />
                Override autodetect: <input type="checkbox" name="override_version" id="override_version" <?cs if:hackinstall.override_version ?>checked="true"<?cs /if ?>/>
            </label>
        </div>
        <div class="buttons">
            <input type="submit" name="update_metadata" value="Update metadata" />
            <input type="submit" name="save_settings" value="Apply changes">
        </div>
    </fieldset>
    <fieldset>
        <legend>Pending Updates</lengend>
        <?cs if:len(hackinstall.updates)>0 ?>
            <fieldset>
                <legend>Plugins</legend>
                <?cs each:plugin = hackinstall.updates.plugins ?>
                    <p>
                        <b><?cs name:plugin ?></b><br />
                        Upgrade from revision <?cs var:plugin.installed ?> to revision <?cs var:plugin.current ?>
                        <input type="checkbox" name="doupdate_<?cs name:plugin ?>" />
                    </p>
                <?cs /each ?>
            </fieldset>
            <div class="buttons">
                <input type="submit" name="update_all" value="Update All" />
                <input type="submit" name="update_selected" value="Update Selected" />
            </div>
        <?cs else ?>
            No pending updates
        <?cs /if ?>
    </fieldset>
</form>

<script type="text/javascript">
<!--
    var override_version = document.getElementById("override_version");
    var change_override = function() {
        document.getElementById("version_field").disabled = ! override_version.checked;
    };
    
    addEvent(override_version, "change", change_override);
//-->
</script>

