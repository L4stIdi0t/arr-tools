import requests


class EmbyAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def _url_builder(self, endpoint, **kwargs):
        url = self.base_url + endpoint
        if len(kwargs) > 0:
            url += "?"
            for key, value in kwargs.items():
                url += f"{key}={value}&"
            url = url[:-1]
        return url

    def _url_extender(self, url, **kwargs):
        if len(kwargs) > 0:
            for key, value in kwargs.items():
                url += f"&{key}={value}"
            url = url[:-1]
        return url

    def _get_request(self, requested_url, method="GET"):
        if method == "GET":
            response = requests.get(
                requested_url, headers={"X-Emby-Token": self.api_key}
            )
        elif method == "POST":
            response = requests.post(
                requested_url, headers={"X-Emby-Token": self.api_key}
            )
        elif method == "DELETE":
            response = requests.delete(
                requested_url, headers={"X-Emby-Token": self.api_key}
            )
        else:
            raise Exception("Method not supported")

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            print(response.url)
            return None

    def test_connection(self):
        url = self._url_builder("/System/Info")
        return self._get_request(url)

    def get_users(self):
        url = self._url_builder("/Users/Query")
        return self._get_request(url)["Items"]

    def get_items(self, recursive=True, **kwargs):
        url = self._url_builder("/Items", recursive=recursive, **kwargs)

        return self._get_request(url)["Items"]

    def get_user_items(self, user_id, recursive=True, **kwargs):
        url = self._url_builder(
            f"/Users/{user_id}/Items", recursive=recursive, **kwargs
        )

        return self._get_request(url)["Items"]

    def get_user_favorites(self, user_id, types=["Movie", "Series"]):
        url_types = ''.join(f'{item}%2C' for item in types)
        url = self._url_builder(
            f"/Users/{user_id}/Items", recursive=True, Filters="IsFavorite", IncludeItemTypes=url_types
        )
        return self._get_request(url)["Items"]

    def get_user_resume(self, user_id):
        url = self._url_builder(f"/Users/{user_id}/Items/Resume", recursive=True, MediaTypes="Video")

        return self._get_request(url)["Items"]

    def get_user_played(self, user_id):
        # Why if querying movie, episode and serie it does not return all series? ...
        items = []
        url = self._url_builder(
            f"/Users/{user_id}/Items", recursive=True, Filters="IsPlayed", IncludeItemTypes="Movie,Episode"
        )
        items += self._get_request(url)["Items"]
        url = self._url_builder(
            f"/Users/{user_id}/Items", recursive=True, Filters="IsPlayed", IncludeItemTypes="Series"
        )
        items += self._get_request(url)["Items"]

        return items
