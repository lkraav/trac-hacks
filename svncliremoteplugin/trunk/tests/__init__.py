from pkg_resources import get_distribution, parse_version

# The tests use the Trac-Hacks repository as a data source.
# You may use a local mirror here to speed up the testing.
# Note that a test will fail if your connection times out.
repo_url = 'https://trac-hacks.org/svn'
# repo_url = 'file:////your/path/to/repository/trac-hacks'
#repo_url = 'file:////Users/cinc/projects/repos/trac-hacks'
# When using Trac 1.0
pre_1_2 = parse_version(get_distribution("Trac").version) < parse_version('1.2')