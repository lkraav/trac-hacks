<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xi="http://www.w3.org/2001/XInclude" xmlns:py="http://genshi.edgewall.org/">
  <xi:include href="layout.html"/>
  <head>
    <title>Screenshots</title>
  </head>

  <body>
    <div id="content" class="screenshot">
      <h1>${screenshots.screenshot.file}</h1>

      <table id="info" summary="Description">
        <tbody>
          <tr>
            <th scope="col">
              ${screenshots.screenshot.name}, ${screenshots.screenshot.width}x${screenshots.screenshot.height} (added by ${screenshots.screenshot.author}, ${screenshots.screenshot.time} ago)
            </th>
          </tr>
          <tr>
            <td class="components">
              <strong>Components:</strong>
              <?cs each:component = screenshots.screenshot.components ?>
                <?cs var:component ?>
              <?cs /each ?>
            </td>
          </tr>
          <tr>
            <td class="versions">
              <strong>Versions:</strong> 
              <?cs each:version = screenshots.screenshot.versions ?>
                <?cs var:version ?>
              <?cs /each ?>
            </td>
          </tr>
          <tr>
            <td class="message">
              <?cs var:screenshots.screenshot.description ?>
            </td>
          </tr>
        </tbody>
      </table>

      <div id="preview">
        <p>
          <a href="${href.screenshots(screenshots.screenshot.id)}?format=raw" title="${screenshots.screenshot.name}">
            <img src="${href.screenshots(screenshots.screenshot.id)}?format=raw" alt="${screenshots.screenshot.description}"
              width="${screenshots.screenshot.width}" height="${screenshots.screenshot.height}"/>
          </a>
        </p>
      </div>

      <div py:if="'SCREENSHOTS_ADMIN' in perm" class="buttons">
        <form method="post" action="${href.screenshots()}">
          <div>
            <input type="submit" name="edit" value="Edit"/>
            <input type="hidden" name="action" value="edit"/>
            <input type="hidden" name="id" value="${screenshots.screenshot.id}"/>
          </div>
        </form>
        <form method="post" action="${href.screenshots()}">
          <div>
            <input type="submit" name="delete" value="Delete"/>
            <input type="hidden" name="id" value="${screenshots.screenshot.id}"/>
            <input type="hidden" name="action" value="delete"/>
          </div>
        </form>
      </div>
    </div>
  </body>
</html>