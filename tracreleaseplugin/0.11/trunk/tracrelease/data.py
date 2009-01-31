# -*- coding: utf8 -*-

import model
import trac.util.datefmt as datefmt
import pprint
import calendar

def _now():
    return datefmt.to_timestamp(datefmt.to_datetime(None))

def get_all(com, sql, *params):
    """Executes the query and returns the (description, data)"""
    db = com.env.get_db_cnx()
    cur = db.cursor()
    desc  = None
    data = None
    try:
        cur.execute(sql, params)
        data = list(cur.fetchall())
        desc = cur.description
        db.commit();
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, params, e));
        db.rollback();
    try:
        db.close()
    except:
        pass

    return (desc, data)

def get_first_row(com, sql, *params):
    """Executes the query and returns the (description, data)"""
    db = com.env.get_db_cnx()
    cur = db.cursor()
    desc  = None
    data = None
    try:
        cur.execute(sql, params)
        data = cur.fetchone()
        desc = cur.description
        db.commit();
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, params, e));
        db.rollback();
    try:
        db.close()
    except:
        pass

    return (desc, data)

def get_all_dict(com, sql, *params):
    """Executes the query and returns a Result Set"""
    desc, rows = get_all(com, sql, *params);
    if not desc:
        return []

    results = []
    for row in rows:
        row_dict = {}
        for field, col in zip(row, desc):
            row_dict[col[0]] = field
        results.append(row_dict)
    return results

def execute_sql(com, sql, *params):
    db = com.env.get_db_cnx()
    cur = db.cursor()

    try:
        cur.execute(sql, params)
        db.commit();
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, params, e));
        db.rollback();
    try:
        db.close()
    except:
        pass
    

    
def findAvailableVersions(com):
    """Find all registered versions"""
    sql = "SELECT name, time, description FROM version ORDER BY time DESC"
    return get_all_dict(com, sql)



def signRelease(com, releaseId, userName):
    """Marks a Release as signed by the indicated user"""
    sql = "UPDATE release_signatures SET sign_date = %s WHERE release_id = %s AND signature = %s"
    execute_sql(com, sql, _now(), releaseId, userName)
    
    
    
    
    
def createRelease(com, name, description, author, planned, tickets, signatures, install_procedures):
    sql = """INSERT INTO releases (version, description, author, creation_date, planned_date) VALUES (%s, %s, %s, %s, %s)"""
    sqlTickets = """INSERT INTO release_tickets (release_id, ticket_id) VALUES (%s, %s)"""
    sqlSignatures = """INSERT INTO release_signatures (release_id, signature) VALUES (%s, %s)"""
    sqlInstallProcedures = """INSERT INTO release_installs (release_id, install_id) VALUES (%s, %s)"""
    sqlInstallFiles = """INSERT INTO release_files (release_id, install_id, file_order, file_name) VALUES (%s, %s, %s, %s)"""

    db = com.env.get_db_cnx()
    cur = db.cursor()
    
    flag = True
    relId = None
    now = _now()
    plannedDateInSeconds = planned and calendar.timegm(planned.utctimetuple()) or None
    
    try:
        cur.execute(sql, (name, description, author, now, plannedDateInSeconds))
    except Exception, e:
        flag = False
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, (name, description, author, now, planned), e));
        db.rollback()
        
    if flag:
        relId = db.get_last_id(cur, 'releases')
        if relId:
            for ticket in tickets:
                ticket = ticket.ticket_id
                try:
                    ticket = int(ticket)
                except:
                    ticket = 0
                    
                if ticket:
                    try:                
                        cur.execute(sqlTickets, (relId, ticket))
                    except Exception, e:
                        flag = False
                        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sqlTickets, (relId, ticket), e));
                        db.rollback()
                        break
                    
        if relId and flag:
            for sign in signatures:
                sign = sign.signature
                if sign:
                    try:    
                        cur.execute(sqlSignatures, (relId, sign))
                    except Exception, e:
                        flag = False
                        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sqlSignatures, (relId, sign), e));
                        db.rollback()
                        break
        
        if relId and flag:
            for inst in install_procedures:
                ## inst is an instance of ReleaseInstallProcedure
                if inst:
                    try:
                        sqlCommand = sqlInstallProcedures
                        sqlParams = "%s" % ([relId, inst.install_procedure.id])
                        cur.execute(sqlInstallProcedures, (relId, inst.install_procedure.id))
                      
                        if inst.install_files:
                            com.log.debug("Files to save:")
                            com.log.debug(inst.install_files)
                            cnt = 1
                            sqlCommand = sqlInstallFiles
                            for arq in inst.install_files:
                                com.log.debug("\tArquivo: %s" % arq)
                                sqlParams = "%s" % ([relId, inst.install_procedure.id, cnt, arq])
                                cur.execute(sqlInstallFiles, (relId, inst.install_procedure.id, cnt, arq))
                                cnt += 1
                                            
                    except Exception, e:
                        flag = False
                        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s' % (sqlCommand, sqlParams, e));
                        db.rollback()
                        break


        if flag:
            com.log.debug("Included... Trying to commit...")
            db.commit();
    try:
        db.close()
    except:
        pass

    if flag:
        return relId
    else:
        return None



def loadDateField(fieldValue):
    return (fieldValue and datefmt.to_datetime(fieldValue) or None)

    
def loadListFromDatabase(com, sql, f, *params):
    """
    Executes the SQL command and fetches all resulting rows. Then passes those rows to
    the f function and returns the resulting list.
    """
    result = []
    db = com.env.get_db_cnx()
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        ret = cur.fetchall()
    except Exception, e:
        com.log.error('data.loadListFromDatabase: There was a problem executing sql: %s\n\twith params: %s\nException: %s' % (sql, params, e));

    try:        
        if ret:
            com.log.debug('data.loadListFromDatabase: result = %s' % pprint.pprint(ret))
            for row in ret:
                result.append(f(row))
    except Exception, e:
        com.log.error('data.loadListFromDatabase(%s) with params [%s]: %s' % (sql, params, e))
        
    try:
        db.close()
    except:
        pass

    return result
        




def loadFromDatabase(com, sql, f, *params):
    """
    Executes the SQL command and fetches only one row. Then passes this row to
    the f function.
    """
    result = None
    db = com.env.get_db_cnx()
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        result = cur.fetchone()
                
    except Exception, e:
        com.log.error('There was a problem executing sql: %s\n\twith params: %s\nException: %s' % (sql, params, e));

    try:
        if result:
            com.log.debug('loadFromDatabase: result = %s' % str(result))
            result = f(result)
    except Exception, e:
        com.log.error('data.loadListFromDatabase(%s) with params [%s]: %s' % (sql, params, e))

        
    try:
        db.close()
    except:
        pass

    return result


   
    
def findAvailableReleases(com):
    """Find all created releases, closed and open"""
    sql = "SELECT id, version, description, author, creation_date, planned_date, install_date FROM releases ORDER BY version DESC"
    f = lambda row: model.Release(row[0], row[1], row[2], row[3],
                                  loadDateField(row[4]),
                                  loadDateField(row[5]),
                                  loadDateField(row[6]))
    result = loadListFromDatabase(com, sql, f)

    return result
    




def getTicket(com, ticketId):
    """Load some data from the indicated ticket"""
    sql = """SELECT t.id, t.summary, t.component, t.type, t.version FROM ticket t WHERE t.id = %s"""
    f = lambda row: model.ReleaseTicket(None, row[0], row[1], row[2], row[3], row[4])
    result = loadFromDatabase(com, sql, f, ticketId)
    
    return result




def getVersionTickets(com, version):
    """Load all tickets that are associated to the indicated version"""
    sql = """SELECT t.id, t.summary, t.component, t.type, t.version FROM ticket t WHERE t.version = %s"""
    f = lambda row: model.ReleaseTicket(None, row[0], row[1], row[2], row[3], row[4])
    result = loadListFromDatabase(com, sql, f, version)
    
    return result






def loadRelease(com, releaseId):
    """Load Release data"""
    sql = "SELECT id, version, description, author, creation_date, planned_date, install_date FROM releases WHERE id = %s"
    f = lambda row: model.Release(row[0], row[1], row[2], row[3], loadDateField(row[4]),
                                  loadDateField(row[5]), loadDateField(row[6]))
    result = loadFromDatabase(com, sql, f, releaseId)
    
    if result:    
        result.tickets = loadReleaseTickets(com, releaseId)
        result.signatures = loadReleaseSignatures(com, releaseId)
        result.install_procedures = loadReleaseInstallProcedures(com, releaseId)
    
    return result






def loadReleaseTickets(com, releaseId):
    com.log.debug("loadReleaseTickets(%s)" % str(releaseId))
    sql = """SELECT rt.release_id,
                    rt.ticket_id,
                    t.summary,
                    t.component,
                    t.type,
                    t.version
             FROM release_tickets rt,
                  ticket t
             WHERE rt.release_id = %s
               AND rt.ticket_id = t.id"""
    
    f = lambda row: model.ReleaseTicket(row[0], row[1], row[2], row[3], row[4], row[5]) 
    return loadListFromDatabase(com, sql, f, releaseId)
    
    
    
    
    
def loadReleaseSignatures(com, releaseId):
    com.log.debug("loadReleaseSignatures(%s)" % str(releaseId))
    """Load all users who should sign this Release."""
    sql = """SELECT rs.release_id,
                    rs.signature,
                    rs.sign_date
             FROM release_signatures rs
             WHERE rs.release_id = %s"""
    
    f = lambda row: model.ReleaseSignee(row[0], row[1], loadDateField(row[2]))
    return loadListFromDatabase(com, sql, f, releaseId)




def loadVersion(com, versionId):
    """Load data from a specific version"""
    sql = "SELECT name, time, description FROM version WHERE name = %s"
    f = lambda row: { 'name': row[0], 'time': loadDateField(row[1]), 'description': row[2] }
    return loadFromDatabase(com, sql, f, versionId)
    
    
def findInstallProcedures(com):
    """Find all available Install Procedureres"""
    sql = "SELECT id, name, description, contain_files FROM install_procedures ORDER BY id"
    f = lambda row: model.InstallProcedures(row[0], row[1], row[2], row[3])
    return loadListFromDatabase(com, sql, f)
 

def loadReleaseInstallProcedures(com, releaseId):
    com.log.debug("loadReleaseInstallProcedures(%s)" % str(releaseId))
    """Load all the Install Procedures associated to a specific release"""
    sql = """SELECT rip.release_id, rip.install_id, ip.name, ip.description, ip.contain_files
             FROM release_installs rip, install_procedures ip
             WHERE ip.id = rip.install_id AND rip.release_id = %s"""

    sqlFiles = """SELECT file_order, file_name FROM release_files WHERE release_id = %s and install_id = %s ORDER BY file_order"""
             
    f = lambda row: model.ReleaseInstallProcedure(row[0], model.InstallProcedures(row[1], row[2], row[3], row[4]))
    ret = loadListFromDatabase(com, sql, f, releaseId)
    if ret:
        f1 = lambda row: row[1]
        for proc in ret:        
            proc.install_files = loadListFromDatabase(com, sqlFiles, f1, releaseId, proc.install_procedure.id)
            
    return ret