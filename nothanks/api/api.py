from flask_restx import Api
from flask import url_for

class ProxiedApi(Api):
    @property
    def specs_url(self):
        '''
        The Swagger specifications absolute url (ie. `swagger.json`)

        :rtype: str
        '''
        return url_for(self.endpoint('specs'), _external=False)

api = ProxiedApi(version='1.0', title='No Thanks! API', description='An API for the No Thanks! game')