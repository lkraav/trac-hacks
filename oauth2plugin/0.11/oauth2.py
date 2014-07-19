from trac.core import *
from trac.web.auth import LoginModule

import re
import time
import urlparse
from oauth2client.client import flow_from_clientsecrets

class OAuth2Plugin(LoginModule):
    def match_request(self, req):
        return re.match("/oauth2callback\??.*", req.path_info) or \
            LoginModule.match_request(self, req)

    def process_request(self, req):
        if req.path_info.startswith("/login"):
            self._do_oauth2_login(req)
        elif req.path_info.startswith("/oauth2callback"):
            self._do_callback(req)
        else:
            LoginModule.process_request(self, req)
        req.redirect(self.env.abs_href())

    def _do_oauth2_login(self, req):
        secrets = self.config.getpath("oauth2", "secrets")
        domain = self.config.get("oauth2", "domain")
       
        flow = flow_from_clientsecrets(secrets, scope="openid email",
                redirect_uri=req.base_url + "/oauth2callback")
        if domain:
            flow.params["hd"] = domain
        req.redirect(flow.step1_get_authorize_url())

    def _do_callback(self, req):
        secrets = self.config.getpath("oauth2", "secrets")
        domain = self.config.get("oauth2", "domain")
       
        flow = flow_from_clientsecrets(secrets, scope="openid email",
                redirect_uri=req.base_url + "/oauth2callback")

        try:
            code = urlparse.parse_qs(req.query_string)["code"][0]
        except:
            raise Exception("Received invalid query parameters.")

        credentials = flow.step2_exchange(code)
        token = credentials.id_token

        if "email" not in token:
            raise Exception("ID token missing email field.")

        if domain:
            if "hd" not in token or token["hd"] != domain:
                raise Exception("Invalid domain.")
       
        try:
            authname = token["email"].split("@")[0]
        except:
            raise Exception("Could not parse username from email.")

        req.environ["REMOTE_USER"] = authname
        LoginModule._do_login(self, req)

