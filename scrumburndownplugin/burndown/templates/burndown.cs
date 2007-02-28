<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="burndown">
 <h1>Burndown Chart</h1>
</div>

<form action="<?cs var:burndown.href ?>" method="post">
    <label for="selected_milestone">Select milestone:</label>
    <select id="selected_milestone" name="selected_milestone">
        <?cs each:mile = milestones ?>
            <option value="<?cs var:mile ?>" <?cs if:selected_milestone == mile ?> selected="selected"<?cs /if ?> >
                <?cs var:mile ?>
            </option>
        <?cs /each ?>
    </select>
    <label for="selected_component">Select component:</label>
    <select id="selected_component" name="selected_component">
        <option>All Components</option>
        <?cs each:comp = components ?>
            <option value="<?cs var:comp ?>" <?cs if:selected_component == comp ?> selected="selected"<?cs /if ?> >
                <?cs var:comp ?>
            </option>
        <?cs /each ?>
    </select>

    <div class="buttons">
        <?cs if:start ?>
            <input type="submit" name="start" value="Start Milestone" />
        <?cs /if ?>
        <input type="submit" value="Show Burndown Chart" />
    </div>
</form>

<br />

<?cs if:draw_graph ?>
    
    <b>Current effort remaining: <?cs var:burndown_data[len(burndown_data) - 1][1] ?> hours</b>
    <br/>
    <br/>
    
<!-- graph code begins here-->
<script type="text/javascript" src="<?cs var:chrome.href ?>/hw/js/line.js"></script>
<script type="text/javascript" src="<?cs var:chrome.href ?>/hw/js/wz_jsgraphics.js"></script>
<div id="myCanvas" style="overflow: auto; position:relative;height:400px;width:800px;"></div>

<script>
    var g = new line_graph();
    
    <?cs each:tuple = burndown_data ?>
        g.add('<?cs var:tuple[0] ?>', <?cs var:tuple[1] ?>);
    <?cs /each ?>
    
    //If called without a height parameter, defaults to 250
    g.render("myCanvas", "hours remaining vs. days of sprint", 300);

</script>
<!-- graph code ends here-->
<?cs /if ?>

<?cs include "footer.cs" ?>
