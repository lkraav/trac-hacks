<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
<?cs include "navigation.cs" ?>

<h1>User Guide</h1>

<h2>1&nbsp;&nbsp;Introduction</h2>

<p>Narcissus is a plugin for Trac that provides an interactive visualisation
for mirroring the activities of small groups over a period of months. The 
activities are measured differently for each resource. Contributions to the 
<a href="<?cs var:trac.href.wiki ?>">wiki</a> and 
<a href="<?cs var:trac.href.browser ?>">Subversion repository</a> are measured 
according to the number of added lines.
<a href="<?cs var:trac.href.report ?>">Tickets</a> are scored according to the 
type of activity, such as creating, accepting, and resolving tickets, as well as 
adding comments at different stages of the task.</p>

<p>Users have the ability to control the value placed in each activity. The
underlying measures of the visualisations are very simple; it is important that
this is clear to the users.</p>

<h2>2&nbsp;&nbsp;Views</h2>

<p>Narcissus provides three views of group activity: the group view, the project
view, and the ticket view. These views can be selected by clicking on the links
provided on the <a href="<?cs var:trac.href.narcissus ?>">visualisation page</a>.
</p>

<h3>2.1&nbsp;&nbsp;Group View</h3>

<p>The group view is the default view displayed. This view has a vertical column
for each member of the group. The activities of each group member are mapped 
along the column. The resource (Subversion, wiki, and tickets) correspond to 
different colours and positions, as indicated by the legend on the information 
panel.</p>

<p>The level of activity on a resource for a given day is given a score from one
to four, with four the highest. The score determines whether a square is pale or 
brightly coloured. Grey indicates there was no activity on that resource on that 
day, by that group member.</p>

<p>At the bottom of the columns is an aggregate summary of activity for each 
group member. The coloured bars indicate the total level of activity for each 
group member. The grey bays indicate the average level for the group. The grey 
bars are semi-transparent, so activity above average has a bright coloured tip, 
and below average has a grey tip.</p>

<h3>2.2&nbsp;&nbsp;Project View</h3>

<p>The project view displays a single vertical column summarising the combined 
activity of all group members. As with the group view described above, each day 
is mapped vertically from bottom to top, each resource is indicated by a 
different colour (provided in the legend), and the level of activity is indicated 
by the brightness of the colour. Grey indicates that there was no activity on 
that resource on that day, by any member of the group.</p>

<p>Unlike the group view, the project view does not provide an aggregate summary 
on the bottom. Since the group as a whole is considered, a total does not provide 
any more information than an average. The average level of activity for each 
resource is depicted by the width of each resource column. The average is 
relative to the span of the project, not to the number of group members. This is 
important for two reasons. First, activity must be maintained throughout the 
project. Secondly, the average is less sensitive to extreme group members. If one 
group member is underperforming, or conversely, dominating the group, their 
activity will not skew the average as it can in the group view.</p>

<h3>2.3&nbsp;&nbsp;Ticket View</h3>

<p>The ticket view displays a history of ticket activity for each group member. 
The visualisation shows a vertical column for each group member. The lifeline of 
each ticket is plotted along the column of the current owner of the ticket, 
showing how long it has been open. Dots are used to indicate the creation, 
resolution, or change in ownership of a ticket, using a dark grey line joining 
the dots to indicate the time span of a ticket, and colour to indicate the group 
member who made the changes. The colours correspond to different group members.</p>

<p>The dot at the bottom of a lifeline indicates the creation of a ticket, and 
the dot at the top indicates the resolution. A dot in the middle of the line 
indicates a change in ownership has occurred. The line is thin by default to show 
that a ticket is active, and the line becomes thicker to show when the owner has 
accepted it. If a line continues right to the top of the visualisation, then it 
was still active on the most recent day being visualised. If a lifeline appears 
as a single dot, then the ticket was created and resolved on the same day.</p>

<h2>3&nbsp;&nbsp;Interactivity</h2>

<p>All three views are completely interactive. The user can click on the components 
of the visualisation to bring up the list of related activities in the details 
section of the information panel. The "clickable" components include the coloured 
squares in the group view, the coloured rectangles in the project view, and the 
ticket lifelines in the ticket view.</p>

<p>The activities listed in the details sections provide a hyperlink to the
actual activity on Trac. Each wiki activity has a hyperlink to the wiki page, 
each ticket activity has a hyperlink to the ticket page, and Subversion activity 
has a hyperlink to the changeset, which shows the actual changes made to the 
source code. The links to Trac enable users to review the activities listed by 
the visualisation, and make a qualitative judgement about the contributions that 
have been made.</p>

<h2>4&nbsp;&nbsp;Scrutability</h2>

<p>The term scrutability refers to the ability to identify why a system behaves 
the way it does. In the context of this visualisation, the users are presented 
with a model of their activity. If the user is able to understand the underlying 
process that generates this information, then the model is scrutable. As discussed 
above, a discrete scoring system is used to determine the level of activity. The 
method of calculating the score may not be obvious to the user, and as such the 
interface has included these details in order to make the visualisations 
scrutable. When the user clicks on any of the components of the group or project 
views, the elements of the score calculation are displayed in the information 
panel beneath the activity details.</p>

<p>The activities are measured differently for each resource. Contributions to 
the wiki and Subversion repository are measured according to the number of added 
lines. Tickets are scored according to the type of activity, such as creating, 
accepting, and resolving tickets, as well as adding comments at different stages 
of the task.</p>

<h2>5&nbsp;&nbsp;User Controls</h2>

<p>The values used to score the level of activity can be changed from the 
<a href="<?cs var:trac.href.configure ?>">configuration page</a>. The default
values are roughly logarithmic. This is useful for groups to cater the scoring
to their particular use of the online tools.</p>

<p>Users can also change the relative value placed in various ticket activities
from the configuration page. The default values assume that accepting a ticket
and closing a ticket are associated with the actual completion of a task by a
user (such as writing source code); and that creating, commenting on, or 
otherwise updating a ticket is associated with general task maintenance.</p>

<?cs include "footer.cs" ?>