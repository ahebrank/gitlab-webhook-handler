from urllib.parse import urlparse
import requests
import json
class GitlabApi:
    base_url = None
    token = None

    def __init__(self, homepage, token):
        self.token = token
        o = urlparse(homepage)
        self.base_url = o.scheme + "://" + o.netloc + "/api/v4/"

    def get_url(self, endpoint):
        if '?' in endpoint:
            parameter_delmiter = "&"
        else:
            parameter_delmiter = "?"
        url = self.base_url + endpoint + parameter_delmiter + "private_token=" + self.token
        return url

    def post(self, endpoint, data):
        r = requests.post(self.get_url(endpoint), data=data)
        return r.ok

    def put(self, endpoint, data):
        r = requests.put(self.get_url(endpoint), data=data)
        return r.ok

    def get(self, endpoint):
        r = requests.get(self.get_url(endpoint))
        return json.loads(r.text)

    def lookup_username(self, email):
        users = self.get("/users?search=" + email)
        if len(users) == 1:
            return users[0]['username']
        return False

    def comment_on_issue(self, project_id, issue_id, comment):
        data = {
            'id': project_id,
            'issue_iid': issue_id,
            'body': comment
        }
        return self.post("/projects/{id}/issues/{issue_iid}/notes".format(**data), data)

    def set_issue_labels(self, project_id, issue_id, labels):
        data = {
            'id': project_id,
            'issue_iid': issue_id,
            'labels': ','.join(labels)
        }
        return self.put("/projects/{id}/issues/{issue_iid}".format(**data), data)

    def get_issue(self, project_id, issue_id):
        data = {
            'id': project_id,
            'issue_iid': issue_id
        }
        return self.get("/projects/{id}/issues/{issue_iid}".format(**data))

    def get_labels(self, project_id):
        labels = self.get("/projects/{id}/labels".format(id=project_id))
        return labels

    def get_boards(self, project_id):
        return self.get("/projects/{id}/boards".format(id=project_id))


