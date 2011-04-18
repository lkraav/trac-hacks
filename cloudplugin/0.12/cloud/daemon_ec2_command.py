#!/bin/python

import sys
import json
import time
from subprocess import Popen, STDOUT, PIPE, CalledProcessError
from daemon import Daemon

class CommandError(CalledProcessError):
    def __init__(self, returncode, cmd, out):
        CalledProcessError.__init__(self, returncode, cmd)
        self.out = out.lstrip()
    def __str__(self):
        return CalledProcessError.__str__(self) + "\n%s" % self.out

class Ec2Commander(Daemon):
    """Executes commands for each node specified by environments and roles."""
    
    def __init__(self):
        Daemon.__init__(self, ['Determining instances..'], "Execute Progress")
        
    def run(self, sysexit=True):
        self.progress.description("Executing: %s" % self.attributes['command'])
        
        # first determine the steps
        ref_field = self.launch_data['node_ref_field']
        environments = self.launch_data['cmd_environments']
        roles = self.launch_data['cmd_roles']
        eq = ' OR '.join(['environment:%s' % e for e in environments])
        rq = ' OR '.join(['role:%s' % r for r in roles])
        q = '(%s) AND (%s)' % (eq,rq)
        self.log.debug('Querying for nodes with query %s' % q)
        nodes,total = self.chefapi.search('node', sort=ref_field, q=q)
        if len(nodes)> 0:
            self.log.debug('Generating steps for %d nodes..' % len(nodes))
            steps = ["Executing for node %s" % n[ref_field] for n in nodes]
            self.progress.steps(steps)
        else:
            self.progress.error("No nodes found for query '%s'" % q)
        
        # Deploy to each instance
        step = 0
        for node in nodes:
            self.progress.start(step)
            host = node['ec2']['public_hostname']
            
            # prepare the command
            self.attributes['host'] = host
            self.attributes['roles_on_host'] = ','.join(node['roles'])
            self.attributes['keypair_pem'] = self.chefapi.keypair_pem
            cmd = self.attributes['command'] % self.attributes
            
            # execute the command
            self._execute(cmd)
            self.progress.done(step)
            step += 1
        
        if sysexit:
            sys.exit(0) # success
    
    def _execute(self, cmd, attempt=1, max=5):
        retry_returncode = int(self.launch_data.get('retry_returncode',0))
        self.log.debug("Running: %s" % cmd)
        p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
        out = p.communicate()[0]
        if retry_returncode and p.returncode==retry_returncode and attempt<max:
            self.log.debug("Retry attempt %d of %d..\n" % (attempt+1,max))
            time.sleep(10)
            self._execute(cmd, attempt+1)
        elif p.returncode != 0:
            raise CommandError(p.returncode, cmd, out)
        else:
            self.log.info("%s\nSuccessfully ran: %s" % (out,cmd))


if __name__ == "__main__":
    daemon = Ec2Commander()
    try:
        if daemon.options.daemonize:
            daemon.start()
        else:
            daemon.run()
    except Exception, e:
            import traceback
            msg = "Oops.. " + traceback.format_exc()+"\n"
            daemon.progress.error(msg)
            daemon.log.error(msg)
            daemon.handler.flush()
            sys.exit(1)
