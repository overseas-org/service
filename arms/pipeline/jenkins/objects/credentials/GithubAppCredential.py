
class GithubAppCredential:
    def __init__(self, app_id, key_path, id="github-app"):
        self.id = id
        self.app_id = app_id
        self.key_path = key_path