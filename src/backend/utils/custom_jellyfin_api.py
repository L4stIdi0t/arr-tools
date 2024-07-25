from utils.custom_emby_api import EmbyAPI


class JellyfinAPI(EmbyAPI):
    def get_users(self):
        url = self._url_builder("/Users")
        return self._get_request(url)
