import pkg_resources

from trac.util.translation import domain_functions

pkg_resources.require('Trac >= 1.2')

_, add_domain, tag_ = domain_functions('tracvote', ('_', 'add_domain', 'tag_'))
