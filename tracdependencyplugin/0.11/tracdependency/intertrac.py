# -*- coding: utf-8 -*-
import re

from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_ctxtnav
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.model import Ticket

from trac.env import open_environment

class InterTrac:

    def __init__(self, config):
        # interTracの設定を取得します．
        self.intertracs0 = {}
        for key, value in config.options('intertrac'):
            # オプションの数のループを回り，左辺値の.を探します．
            idx = key.rfind('.')  
            if idx > 0: # .が無い場合はショートカットですが無視します
                # .があった場合の処理
                # 左辺値を分割します
                prefix, attribute = key[:idx], key[idx+1:]
                # すでにあるものをとってきます無ければ新規で作成
                intertrac = self.intertracs0.setdefault(prefix, {})
                # 左辺値のピリオド以降をキーで右辺値を登録
                intertrac[attribute] = value
                # プロジェクト名を設定します．(注：すべて小文字になっている) 
                intertrac['name'] = prefix

        self.intertracs = []
        # 取得したinterTrac設定の名前が小文字になっているので元に戻します．
        # ついでに，プロジェクトの一覧表示用のデータを作成しておきます．
        # 結局はintertrac['label'] 設定することにしたので意味はないのですが，つくっちゃったのでこのままにします．
        for prefix in self.intertracs0:
            intertrac = self.intertracs0[prefix]
            # Trac.iniのパスを取得します
            path = intertrac.get('path', '')
            # trac.iniをオープンする
            project = open_environment(path, use_cache=True)
            # 名前をtrac.iniのプロジェクト名で置き換えます．
#            intertrac['name'] = project.project_name 
            intertrac['name'] = intertrac['label'] 
            # プロジェクトの一覧表示用のデータを作成します．
            url = intertrac.get('url', '')
            title = intertrac.get('title', url)
            name = project.project_name
            self.intertracs.append({'name': name, 'title': title, 'url': url, 'path': path})

    def get_projects(self):
        return self.intertracs0

    def project_information(self):
        return self.intertracs

    def create_links(self, sql, log):
        # 後続チケットまたは，子チケットへのリンクを作ります．
        links = []
        log.debug("create_links 000")
        intertracs0 = self.get_projects()
        log.debug("create_links 001")
        for prefix in intertracs0:
            log.debug("create_links prefix = %s" % prefix)
            intertrac = intertracs0[prefix]
            path = intertrac.get('path', '')
            log.debug("create_links path = %s" % path)
            try:
                project = open_environment(path, use_cache=True)
                db = project.get_db_cnx()
                cursor = db.cursor();
                cursor.execute(sql)
                tickets=[]
                log.debug("create_links 002")
                for id, type, summary, owner, description, status in cursor:
                    log.debug("create_links 003")
                    url = intertrac.get('url', '') + '/ticket/' + str(id)
                    log.debug("create_links url ^ %s" % url)
                    dep_url = intertrac.get('url', '') + '/dependency/ticket/' + str(id)
                    log.debug("create_links dep_url ^ %s" % dep_url)
                    ticket = intertrac['name'] + ':#' + str(id)
                    log.debug("create_links ticket ^ %s" % ticket)
                    link = links.append({'ticket':ticket, 'title':summary, 'url':url, 'dep_url':dep_url, 'status':status})
                
            except Exception, e:
                pass
            # オープンできない場合もあるのでエラー処理が必要
        return links

    def linkify_ids_b(self, env, req, ids, label1, log):
        # チケットの表示のページでinterTracリンクの表示するための元を作る
        intertracs0 = self.intertracs0
        data = []
        if ids is None:
            return data
        tickets = ids.split(',') #なにもない場合はエラーになるのでifが必要
        data.append(label1)
        for ticket in tickets:
            # ,で分割した文字列に対して処理を行います
            ticket = ticket.strip() # 前後の空白を削除します
            log.debug("id = %s" % ticket)
            if len(ticket) > 0:
                log.debug("id = %s" % ticket)
                idx = ticket.rfind(':#') # プロジェクト名とチケット番号に分割します
                log.debug("idx = %s" % str(idx))
                if idx > 0: # 存在した場合
                    project_name, id = ticket[:idx], ticket[idx+2:]
                    # 依存関係を指定しているか確認する 例:(FF)
                    idx = id.rfind('(')
                    if idx > 0:
                        # 指定されていたならそれはidに含まない
                        id = id[:idx]
                    # InterTracの設定のキーは小文字
                    intertrac = intertracs0[project_name.lower()]
                    path = intertrac.get('path', '')
                    # TODO:　オープンできない場合もあるのでエラー処理が必要
                    project = open_environment(path, use_cache=True)
                    url = intertrac.get('url', '') + '/ticket/' + id
                    tkt = Ticket(project, id)
                    if not url:
                        url = req.href.ticket(tkt.id)
                    data.append(tag.a('%s'%ticket, href=url, class_='%s ticket'%tkt['status'], title=tkt['summary']))
                else: # 存在しない場合
                    log.debug("idx = %s" % str(idx))
                    data.append('%s'%ticket)
                    # 複数ある場合は", "を追加する
                data.append(', ')
        if data:
            # 最後のカンマを削除する．
            del data[-1]
        data.append(tag.br())
        log.debug("???????")
        return data

    def linkify_ids(self, env, req, ids, label1, label2, tickets2, log):
        # チケットの表示のページでinterTracリンクの表示するための元を作る
        intertracs0 = self.intertracs0
        log.debug("linkify_ids 001")
        data = self.linkify_ids_b(env, req, ids, label1, log)
        log.debug("linkify_ids 002")
        data.append(label2)
        log.debug("linkify_ids 003")
        for ticket in tickets2:
            log.debug("linkify_ids 004")
            tkt = ticket['ticket']
            url = ticket['url']
            log.debug("linkify_ids url = %s" % url)
            status = ticket['status']
            log.debug("linkify_ids status = %s" % status)
            title1 = ticket['title']
            log.debug("linkify_ids title1 = %s" % title1)
            data.append(tag.a('%s'%tkt, href=url, class_='%s ticket'%status, title=title1))
            data.append(', ')
            log.debug("linkify_ids 005")
        if data:
            # リストになにもない場合はラベル，ある場合は最後のカンマを削除する．
            del data[-1]
        log.debug("linkify_ids 006")
        return tag.span(*data)

    def get_link(self, ids):
        links = []
        intertracs0 = self.intertracs0
        if ids is None: #idになにも入ってない場合はエラーになるのでifが必要
            return links
        tickets = ids.split(',')
        for ticket in tickets:
            # ,で分割した文字列に対して処理を行います
            ticket = ticket.strip() # 前後の空白を削除します
            idx = ticket.rfind(':#') # プロジェクト名とチケット番号に分割します
            if idx > 0: # 存在した場合
                project_name, id = ticket[:idx], ticket[idx+2:]
                # 依存関係を指定しているか確認する 例:(FF)
                idx = id.rfind('(')
                if idx > 0:
                    # 指定されていたならそれはidに含まない
                    id = id[:idx]
                # InterTracの設定のキーは小文字
                intertrac = intertracs0[project_name.lower()]
                path = intertrac.get('path', '')
                # TODO:　オープンできない場合もあるのでエラー処理が必要
                project = open_environment(path, use_cache=True)
                url = intertrac.get('url', '') + '/ticket/' + id
                dep_url = intertrac.get('url', '') + '/dependency/ticket/' + id
                tkt = Ticket(project, id)
                status = tkt['status']
                title = tkt['summary']
                link = links.append({'ticket':ticket, 'title':title, 'url':url, 'dep_url':dep_url, 'status':status})
        return links
