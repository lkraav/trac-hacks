#!/usr/bin/env python
'''
Usage: %s [-m commitmsg] [-u username] repos-url repos-url

Move a file or directory within a Subversion repository
'''

import getopt
import os
import sys

from svn import core, fs, repos, client

def log_message_func(items, pool):
    '''Return a commit log message
    '''
    return "Test log message"
    
def svn_move(src_path, dst_path, username='', commitmsg=''):
    '''Move src_path to dst_path, where each is the url to a file or directory
    in a Subversion repository. Apply the change as username, and log with 
    commitmsg.
    '''
    src_path = core.svn_path_canonicalize(src_path)
    dst_path = core.svn_path_canonicalize(dst_path)
    print src_path
    print dst_path
    
    force = False
    move_as_child = False
    make_parents = False
    revprop_tbl = None
    
    client_ctx = client.create_context()
    client_ctx.log_msg_func3 = client.svn_swig_py_get_commit_log_func
    client_ctx.log_msg_baton3 = log_message_func
    auth_providers = [client.svn_client_get_simple_provider(),
                      client.svn_client_get_username_provider(),
                     ]
    client_ctx.auth_baton = core.svn_auth_open(auth_providers)
    
    commit_info = client.svn_client_move3(src_path,
                                          dst_path,
                                          int(force), 
                                          #move_as_child,
                                          #make_parents,
                                          #revprop_tbl,
                                          client_ctx,
                                          )
    """
    svn_client_move5(svn_commit_info_t commit_info_p, 
        apr_array_header_t src_paths, 
        char dst_path, 
        svn_boolean_t force, 
        svn_boolean_t move_as_child, 
        svn_boolean_t make_parents, 
        apr_hash_t revprop_table, 
        svn_client_ctx_t ctx, 
        apr_pool_t pool) -> svn_error_t
    """

def usage(prog_name):
    print (__doc__ % prog_name).strip('\n')
    
def main():
    prog_name = sys.argv[0]
    opts, args = getopt.getopt(sys.argv[1:], 'm:u:')
    if len(args) != 2:
        usage(prog_name)
        sys.exit(1)

    username = commitmsg = ""

    for name, value in opts:
        if name == '-u':
            username = value
        if name == '-m':
            commitmsg = value
    
    svn_move(args[0], args[1], username, commitmsg)

if __name__ == '__main__':
    main()
