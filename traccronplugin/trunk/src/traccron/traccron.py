# -*- encoding: UTF-8 -*-

'''
Created on 12 oct. 2010

@author: thierry
'''
from trac.core import *
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from threading import Timer
from time import  time, localtime



class ICronTask(Interface):
    """
    Interface for component task
    """
    
    def wake_up(self):
        """
        Call by the scheduler when the task need to be executed
        """
        raise NotImplementedError
    
    def getId(self):
        """
        Return the key to use in trac.ini to cinfigure this task
        """
        raise NotImplementedError
    
    def getDescription(self):
        """
        Return the description of this task to be used in the admin panel.
        """
        raise NotImplementedError


class Core(Component):    
    """
    Main class of the Trac Cron Plugin. This is the entry point
    for Trac plugin architecture
    """    
    
    implements(IAdminPanelProvider, ITemplateProvider)
    
    cron_tack_list = ExtensionPoint(ICronTask)
    
    
    
    def __init__(self,*args,**kwargs):
        """
	    Intercept the instanciation to start the ticker
        """        
        Component.__init__(self, *args, **kwargs)
        self.ticker = None
        self.cronconf = CronConfig(self.env)
        self.supported_schedule_type = [DailyScheduler(self.getCronConf())]
        self.webUi = WebUi(self)        
        self.apply_config()        

        
    def apply_config(self, wait=False):
        """
        Read configuration and apply it
        """
        # stop existing ticker if any
        if self.ticker is not None:
            self.ticker.cancel(wait=wait)

        if self.getCronConf().get_ticker_enabled():            
        	self.ticker = Ticker(self.env,self.getCronConf().get_ticker_interval(), self.check_task)

            

    def getCronConf(self):
        """
        Return the configuration for TracCronPlugin
        """
        return self.cronconf
    
    def getTaskList(self):
        """
        Return the list of existing task
        """
        return self.cron_tack_list
    
    def getSupportedScheduleType(self):
        """
        Return the list of supported schedule type
        """
        return self.supported_schedule_type
    
    def check_task(self):
        """
        Check if any task need to be executed. This method is called by the Ticker.
        """
        # store current time
        currentTime = localtime(time())        
        for task in self.cron_tack_list:
            # test current time with task planing            
            for schedule in self.supported_schedule_type:
                # run task if needed
                if schedule.isTriggerTime(task, currentTime):
                    task.wape_up()                       

        
    # IAdminPanel interface
    
    def get_admin_panels(self, req):
       return self.webUi.get_admin_panels(req)


    def render_admin_panel(self, req, category, page, path_info):
        return self.webUi.render_admin_panel(req, category, page, path_info)

    # ITemplateProvider interface
    def get_htdocs_dirs(self):
        return self.webUi.get_htdocs_dirs()


    def get_templates_dirs(self):
       return self.webUi.get_templates_dirs()
    
        
        
 
class CronConfig():
    """
    This class read and write configuration for TracCronPlugin
    """
    
    TRACCRON_SECTION = "traccron"
    
    TICKER_ENABLED_KEY = "ticker_enabled"
    TICKER_ENABLED_DEFAULT = "False"
    
    TICKER_INTERVAL_KEY = "ticker_interval"
    TICKER_INTERVAL_DEFAULT = 1 #minutes
    

    def __init__(self, env):
        self.env = env
            
    def get_ticker_enabled(self):
        return self.env.config.getbool(self.TRACCRON_SECTION, self.TICKER_ENABLED_KEY, self.TICKER_ENABLED_DEFAULT)

    def set_ticker_enabled(self, value):
        self.env.config.set(self.TRACCRON_SECTION, self.TICKER_ENABLED_KEY, value)
    
    def get_ticker_interval(self):
        return self.env.config.getint(self.TRACCRON_SECTION, self.TICKER_INTERVAL_KEY, self.TICKER_INTERVAL_DEFAULT)
    
    def set_ticker_interval(self, value):
        self.env.config.set(self.TRACCRON_SECTION, self.TICKER_INTERVAL_KEY, value)
    
    def get_schedule_value(self, task, schedule_type):
        self.env.config.get(self.TRACCRON_SECTION, task.getId() + "." + schedule_type.getId(), None)

    def set_schedule_value(self, task, schedule_type, value):
        self.env.config.set(self.TRACCRON_SECTION, task.getId() + "." + schedule_type.getId(), value)
    
    def set_value(self, key, value):
        self.env.config.set(self.TRACCRON_SECTION, key, value)
    
    def remove_value(self, key):
        self.env.config.remove(self.TRACCRON_SECTION, key)
    
    def save(self):
        self.env.config.save()

class WebUi(IAdminPanelProvider, ITemplateProvider):
    """
    Class that deal with Web stuff. It is the both the controller and the page builder.
    """
    def __init__(self, core):        
        self.env = core.env
        self.cron_task_list = core.getTaskList()
        self.cronconf = core.getCronConf()
        self.all_schedule_type = core.getSupportedScheduleType()
        self.core = core
    
    def get_admin_panels(self, req):
        if ('TRAC_ADMIN' in req.perm) :
            yield ('tracini', 'trac.ini', 'cron_admin', u'Trac Cron')


    def render_admin_panel(self, req, category, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        
        data = {}
        
        if req.method == 'POST':
            if 'save' in req.args:          
                
                arg_name_list = [self.cronconf.TICKER_ENABLED_KEY,self.cronconf.TICKER_INTERVAL_KEY]
                for task in self.cron_task_list:                            
                    task_id = task.getId()                                            
                    for schedule in self.all_schedule_type:
                        arg_name_list.append(task_id + "." + schedule.getId())        
                
                for arg_name in arg_name_list:
                    arg_value = req.args.get(arg_name,"").strip()
                    self.env.log.debug("receive req arg "+ arg_name + "=[" + arg_value + "]")
                    if (arg_value == ""):
                        self.cronconf.remove_value(arg_name)                        
                    else:
                        self.cronconf.set_value(arg_name, arg_value)                  
                
                self.cronconf.save()
                self.core.apply_config(wait=True)
                req.redirect(req.abs_href.admin(category, page))
        else:            
            
            data.update({
                          self.cronconf.TICKER_ENABLED_KEY:self.cronconf.get_ticker_enabled(),
                          self.cronconf.TICKER_INTERVAL_KEY: self.cronconf.get_ticker_interval()                         
                          })
            
            task_list = []
            
            for task in self.cron_task_list:
                task_data = {}
                
                task_data['id'] = task.getId()
                task_data['description'] = task.getDescription()
                
                all_schedule_value = {}
                for schedule in self.all_schedule_type:
                    value = self.cronconf.get_schedule_value(task, schedule)
                    if value :
                        all_schedule_value[schedule.getId()] = value
                    else:
                        all_schedule_value[schedule.getId()] = ""
                task_data['schedule_list'] = all_schedule_value                        
                                        
                task_list.append(task_data)
            
            data['task_list'] = task_list
            return 'cron_admin.html', data
                

    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # internal method
    

class SchedulerType():
    """
    Define a sort of scheduling. Base class for any scheduler type implementation
    """   
    
    def __init__(self, cronconf):
        self.cronconf = cronconf
        
    def getId(self):
        """
        Return the id to use in trac.ini for this schedule type
        """
        raise NotImplementedError
    
    def isTriggerTime(self, task, currentTime):
        """
        Test is accordingly to this scheduler and given currentTime, is time to fire the task
        """
        # read the configuration value for the task
        schedule_value = self._get_task_schedule_value(task)
        return self.compareTime(currentTime, schedule_value)
    
    def compareTime(self, currentTime, schedule_value):
         """
         Test is accordingly to this scheduler, given currentTime and schedule value,
         is time to fire the task.
         currentTime is a structure computed by time.localtime(time())
         scheduled_value is the value of the configuration in trac.ini      
         """
         raise NotImplementedError
    
    def _get_task_schedule_value(self, task):
        return self.cronconf.get_schedule_value(task, self)
    



class DailyScheduler(SchedulerType):
    """
    Scheduler that trigger a task one a day based uppon a defined time
    """
    
    def __init__(self, cronconf):
        SchedulerType.__init__(self, cronconf)
    
    def getId(self):
        return "daily"
    
    def compareTime(self, currentTime, schedule_value):        
        # compare value with current
        if schedule_value:
            return schedule_value == str(currentTime.tm_hour) + str(currentTime.tm_min)
        else:
            return False
         

class Ticker():
    """
    A Ticker is simply a simply timer that will repeatly wake up.
    """
    
    
    def __init__(self, env, interval, callback):
        """
        Create a new Ticker.
        env : the trac environnement
        interval: interval in minute
        callback: the function callback to call o every wake-up
        """
        self.env = env
        self.interval = interval
        self.callback = callback
        self.timer = None
        self.create_new_timer()
        
    def create_new_timer(self, wait=False):
        """
        Create a new timer before killing existing one if required.
        wait : if True the current thread wait until running task finished. Default is False
        """
        if (self.timer != None):
            self.timer.cancel()
            if ( wait ):
                self.timer.join()            
        
        self.timer = Timer(self.interval * 60 , self.wake_up)
        self.timer.start()

    def wake_up(self):
        self.callback()
        self.create_new_timer()
        
    
    def cancel(self, wait=False):
        self.timer.cancel()
        if (wait):
            self.timer.join()


class HeartBeatTask(Component,ICronTask):
    """
    This is a simple task for testing purpose.
    It only write a trace in log a debug level
    """
    
    implements(ICronTask)
    
    def wake_up(self):
        self.env.log.debug("Heart beat: boom boom")
    
    def getId(self):
        return "heart_beat"
    
    def getDescription(self):
        return self.__doc__
        
    
    