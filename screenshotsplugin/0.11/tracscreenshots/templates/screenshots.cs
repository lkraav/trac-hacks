<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xi="http://www.w3.org/2001/XInclude" xmlns:py="http://genshi.edgewall.org/">
  <xi:include href="layout.html"/>
  <head>
    <title>Screenshots</title>
  </head>

  <body>
    <div id="content" class="screenshots">
      <div class="title">
        <h1>${screenshots.title}</h1>
      </div>

      <xi:include href="${screenshots.content_template}"/>

      <div py:if="'SCREENSHOTS_ADMIN'in perm" class="buttons screenshot_buttons">
        <form method="post" action="${href.screenshots()}">
          <div>
            <input type="submit" name="add" value="Add"/>
            <input type="hidden" name="action" value="add"/>
            <input type="hidden" name="index" value="${screenshots.index}"/>
          </div>
        </form>
        <form py:if="len(screenshots) > 0 and index" method="post" action="${href.screenshots()}">
          <div>
            <input type="submit" name="edit" value="Edit"/>
            <input type="hidden" name="action" value="edit"/>
            <input type="hidden" name="id" value="${screenshots.id}"/>
            <input type="hidden" name="index" value="${screenshots.index}"/>
          </div>
        </form>
        <form py:if="len(screenshots) > 0 and index" method="post" action="${href.screenshots()}">
          <div>
            <input type="submit" name="delete" value="Delete"/>
            <input type="hidden" name="id" value="${screenshots.id}"/>
            <input type="hidden" name="index" value="${screenshots.index}"/>
            <input type="hidden" name="action" value="delete"/>
          </div>
        </form>
      </div>

      <div py:if="'SCREENSHOTS_FILTER' in perm" class="filter">
        <form method="post" action="${href.screenshots()}">
          <fieldset>
            <legend>
              Display filter:
            </legend>

            <fieldset>
              <legend>
                Components:
              </legend>

              <div>
                <py:choose py:for="component in screenshots.components">
                  <input py:when="screenshots.enabled_components[component.name]" type="checkbox" name="components" value="${component.name}" checked="yes">
                    ${component.name}
                  </input>
                  <input py:otherwise="" type="checkbox" name="components" value="${component.name}">
                    ${component.name}
                  </input>
                </py:choose>
                <input type="button" name="all" value="All" onclick="check_all('components', true)"/>
                <input type="button" name="none" value="None" onclick="check_all('components', false)"/>
              </div>
            </fieldset>

            <fieldset>
              <legend>
                Versions:
              </legend>

              <div>
                <py:choose py:for="version in screenshots.versions">
                  <input py:when="screenshots.enabled_versions[version.name]" type="checkbox" name="versions" value="${version.name}" checked="yes">
                    ${version.name}
                  </input>
                  <input py:otherwise="" type="checkbox" name="versions" value="${version.name}">
                    ${version.name}
                  </input>
                </py:choose>
                <input type="button" name="all" value="All" onclick="check_all('versions', true)"/>
                <input type="button" name="none" value="None" onclick="check_all('versions', false)"/>
              </div>
            </fieldset>

            <div class="buttons">
              <input type="submit" name="filter" value="Apply Filter"/>
              <input type="hidden" name="action" value="filter"/>
            </div>

          </fieldset>
        </form>
      </div>
    </div>
  </body>
</html>
