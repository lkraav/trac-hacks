<h3>Plugins</h3>

<?cs if:hackinstall.message ?>
<div style="background-color: red"><?cs var:hackinstall.message ?></div>
<?cs /if ?>

<form method="post">
<table>
<tr><td>Name</td><td>Current</td></tr>
<?cs each:plugin = hackinstall.plugins ?>
<tr>
    <td><?cs name:plugin ?></td>
    <td><?cs var:plugin.current ?></td>
    <td><input type="submit" name="download_<?cs name:plugin ?>" value="Download" /></td>
    <td><input type="submit" name="install_<?cs name:plugin ?>" value="Install" /></td>
</tr>
<?cs /each ?>
</table>
</form>
