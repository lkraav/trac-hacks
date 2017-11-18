from subprocess import Popen, PIPE

from trac.wiki.macros import WikiMacroBase

author = "Salvador Fandino"
version = "1.0 ($Rev$)"
url = "https://trac-hacks.org/wiki/PerlPodMacro"


class PodMacro(WikiMacroBase):
    """Converts from Perl Plain Old Documentation format (POD) to HTML"""

    def expand_macro(self, formatter, name, args):
        pod2wiki = Popen(['/usr/bin/pod2html'], cwd='/tmp',
                         stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = pod2wiki.communicate(args.encode('latin1'))
        html = stdout.decode('latin1')

        return html[html.find('>', html.find('<body'))+1:html.find('</body>')].strip()
