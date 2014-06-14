from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.chrome import ITemplateProvider
import jenkinsapi
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import (NoBuildData)


class TracJenkinsPlugin(Component):

    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    def list_all_jobs(self, jenk):
        joblist = jenk.keys()
        return joblist

    def get_job_data(self, jenk, joblist):
        jobreturn = []
        for job in joblist:
            jobdata = {}
            jobdata['job'] = job
            current_job = jenk.__getitem__(job)
            last_build = ''
            result = ''
            try:
                last_build = current_job.get_last_completed_build()
                result = last_build.get_status()
            except NoBuildData:
                last_build = 'No Complete Job'
                result = 'None'
            jobdata['lastbuild'] = last_build
            jobdata['buildresult'] = result
            jobreturn.append(jobdata)
        return jobreturn

    def get_build_data(self, jenk, job):
        current_job = jenk.__getitem__(job)
        build_ids = current_job.get_build_ids()
        for theID in build_ids:
            build_data = {}
            build = current_job.get_build(theID)
            build_data['name'] = build.name
            build_data['result'] = build.get_status()
            build_data['time'] = build.get_timestamp()
            build_data['buildnr'] = theID
            yield build_data

    def get_timestamp(self, current_build):
        return current_build.get_timestamp()

    def get_console_log(self, current_build):
        return current_build.get_console()

    def get_build_result(self, current_build):
        return current_build.get_status()

    def get_build_name(self, current_build):
        return current_build.name

    def get_user_name(self, current_build):
        return current_build.get_actions()['causes'][0]['userName']

    def get_builder_desc(self, current_build):
        return current_build.get_actions()['causes'][0]['shortDescription']

    def get_latest_build(self, jenk, job):
        current_job = jenk.__getitem__(job)
        return current_job.get_last_completed_build()

    def do_build(self, jenk, job):
        current_job = jenk.__getitem__(job)
        current_job.invoke()

    def remove_job(self, jenk, job):
        jenk.delete_job(job)

    def add_job(self, jenk, name):
        jenk.create_job(name)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return[]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'jenkins'

    def get_navigation_items(self, req):
        yield ('mainnav', 'jenkins',
               html.A('Jenkins', href=req.href.jenkins()))

    # IRequestHandler methods
    def match_request(self, req):
        if (req.path_info.startswith('/jenkins')):
            return True
        return False

    def process_request(self, req):
        jenk = Jenkins('http://localhost:8080')
        if (req.path_info.endswith('/invoke')):
            current_job = req.args['job']
            self.do_build(jenk, current_job)
            data = {'current_job': current_job}
            return 'invoke.html', data, None
        elif (req.path_info.endswith('/removejob')):
            current_job = req.args['job']
            self.remove_job(jenk, current_job)
            data = {'current_job': current_job}
            return 'removejob.html', data, None
        elif (req.path_info.startswith('/jenkins/job/build')):
            buildnr = req.args['buildnr']
            current_job = req.args['current_job']
            job = jenk.__getitem__(current_job)
            current_build = job.get_build(int(buildnr))
            logdata = self.get_console_log(current_build)
            time = self.get_timestamp(current_build)
            result = self.get_build_result(current_build)
            name = self.get_build_name(current_build)
            user_name = self.get_user_name(current_build)
            builder_desc = self.get_builder_desc(current_build)
            data = {'log': logdata, 'buildnr': buildnr,
                    'currentjob': current_job, 'time': time,
                    'result': result, 'buildname': name, 'user': user_name,
                    'builder_desc': builder_desc}
            return 'build.html', data, None
        elif (req.path_info.startswith('/jenkins/job')):
            current_job = req.args['job']
            build_data = self.get_build_data(jenk, current_job)
            data = {'builds': build_data, 'currentjob': current_job}
            return 'jobs.html', data, None
        elif (req.path_info.startswith('/jenkins')):
            alljobs = self.list_all_jobs(jenk)
            jobdata = self.get_job_data(jenk, alljobs)
            data = {'jobdata': jobdata}
            return 'start.html', data, None
        return '404.html', data, None
