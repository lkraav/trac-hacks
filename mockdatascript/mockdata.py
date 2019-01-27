setup(name = 'MocklData',
      version = 1.0,
      description = "Create mock data for a configurable amount of wiki pages and tickets",
      keywords = 'Trac',
      license = 'BSD-3 license',
)

from trac.env import Environment
from trac.wiki.model import WikiPage
from trac.ticket.model import Ticket
from trac.ticket.model import Milestone
import datetime
import pytz
import random
import sys

# checks if milestone exists 
def checkMilestone(ms):
   
    try:
    	Milestone(Environment(path), ms)
        return True
    except:
        return False

user inputs
path = raw_input("Enter your project full path, example => /root/trac/tracenv: ")

# trac environment
try:
    env = Environment(path)
except:
    print("Trac project " + str(path) + " does not exists, please try again.")
    sys.exit()

milestones = input("Enter number of milestones to generate: ")
tickets = input("Enter number of tickets to generate: ")
wikis = input("Enter number of wiki pages to generate: ")

# wiki page text from lorem ipsum
texts = ['Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet odio quam. Fusce dapibus lorem leo, sit amet scelerisque nibh accumsan id. Curabitur blandit, risus ut tincidunt auctor, ante ex consequat justo, eget pharetra leo lectus at diam. Donec eu libero nulla. Integer interdum rhoncus mauris id efficitur. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque faucibus ut libero ac venenatis. In malesuada vel ligula nec consectetur. Maecenas quis libero vehicula, accumsan massa sit amet, bibendum nisl. Donec velit urna, pulvinar ut nulla at, convallis dapibus justo. Ut vitae sollicitudin mi. In laoreet sodales viverra. Donec dolor leo, tempor non fermentum eu, malesuada ac mi. Phasellus sed ex ex. Aliquam ante urna, maximus eu porttitor nec, porttitor ac nibh. Praesent vel volutpat neque, nec sagittis massa.', 'Duis ornare quam eget luctus lobortis. Duis malesuada nec dui nec pulvinar. Donec eget dignissim dolor, maximus pellentesque lorem. Nullam eleifend luctus risus ut dignissim. Ut ut dapibus leo. Donec at libero tempor, ullamcorper diam sit amet, varius diam. Pellentesque at neque cursus, consectetur lacus interdum, tristique sem. Fusce tempor sed elit at vestibulum.', 'Donec et metus tempor enim tincidunt tristique eu eu nulla. Phasellus finibus turpis eget tellus maximus dictum. Nullam sollicitudin, enim vitae placerat vestibulum, libero erat placerat ante, non ornare nisl dui porta dolor. Maecenas pulvinar pulvinar ex ac ultrices. Duis lectus lectus, finibus a mattis et, accumsan eget ipsum. Ut sed sem ligula. Etiam suscipit, diam et venenatis accumsan, ipsum justo feugiat ligula, et sagittis purus arcu nec libero. Phasellus in risus eleifend, ultricies ipsum sed, malesuada tellus. In arcu ipsum, fermentum vitae ultrices tincidunt, ultricies ut nibh. Vivamus in commodo felis. Morbi tortor erat, blandit non urna ut, finibus ullamcorper odio. Nunc et odio tortor. Fusce non felis efficitur, viverra nisl vel, facilisis felis. Nullam sit amet erat in diam vulputate semper in a nisl.', 'Maecenas a porta ex. Etiam eget lorem eget turpis scelerisque pulvinar. Sed mollis, purus nec scelerisque consectetur, nibh mauris pharetra nisi, non sagittis sem ipsum tincidunt quam. Quisque turpis mi, imperdiet vel gravida eu, placerat a nulla. Nulla vel nunc sed mi pretium pretium. Ut non ipsum ac tortor ultricies congue ultricies eget ante. Aliquam tincidunt congue justo, volutpat placerat tortor porttitor suscipit. Quisque est odio, pulvinar non orci ut, accumsan pharetra mauris. Nunc aliquet erat sit amet turpis aliquam, et dictum quam iaculis. Cras est eros, dictum sit amet orci id, sodales venenatis metus. Phasellus velit massa, cursus sit amet iaculis non, aliquet eget sem. In vel luctus ipsum. Fusce porta sem euismod justo eleifend']

# store milestones to letter assign for tickets
ticketMs = []

# trac project milestone due date
date = datetime.datetime.utcnow()

# add timezone
if(date.tzinfo == None):
    timezone = pytz.timezone("Europe/London")
    date = timezone.localize(date)

# due date
date += datetime.timedelta(days=30)

# create milestone
for i in range(milestones):
	
    # generate random word and assign as name to milestones
    ms = Milestone(env)
    ms.name = texts[random.randrange(len(texts))]
    
    while(checkMilestone(ms.name)):         
         ms.name += texts[random.randrange(len(texts))]

    ticketMs.append(ms.name)
    ms.due = date
    ms.description = texts[random.randrange(len(texts))]
    ms.insert()
print(str(milestones) + " milestones added")

# create tickets
for k in range(tickets):
    if(len(ticketMs) == 0):
       ticketMs.append("milestone1")
    tkt = Ticket(env)
    tkt['reporter'] = texts[random.randrange(len(texts))]
    tkt['summary'] = texts[random.randrange(len(texts))]
    tkt['description'] = texts[random.randrange(len(texts))]
    tkt['status'] = 'new'
    tkt['milestone'] = ticketMs[random.randrange(len(ticketMs))]
    tkt.insert()
print(str(tickets) + " tickets added")

# create wiki pages
for j in range(wikis):
    page = WikiPage(env, texts[random.randrange(len(texts))])

    while(page.exists):         
         page = WikiPage(env, texts[random.randrange(len(texts))] + texts[random.randrange(len(texts))])

    if(not(page.exists)):

        page.text = texts[random.randrange(len(texts))]
        try:
             page.save(author=texts[random.randrange(len(texts))], comment=texts[random.randrange(len(texts))])
            
        except:
            print("Could not generate wiki pages, please try replacing /usr/lib/python2.7/dist-packages/trac/wiki/model.py with updated model.py or upgrade to the latest Trac version")
            sys.exit()
         
print(str(wikis) + " wiki-pages added")
