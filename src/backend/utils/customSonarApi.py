from pyarr import SonarrAPI
from pyarr.types import JsonObject


class customSonarAPI(SonarrAPI):
    def upd_series_editor(self, data: JsonObject) -> JsonObject:
        """The Updates operation allows to edit properties of multiple movies at once

        Args:
            data (JsonObject): Updated movie information::

                {"movieIds":[28],"tags":[3],"applyTags":"add"}
                {"movieIds":[28],"monitored":true}
                {"movieIds":[28],"qualityProfileId":1}
                {"movieIds":[28],"minimumAvailability":"inCinemas"}
                {"movieIds":[28],"rootFolderPath":"/defaults/"}

        Returns:
            JsonArray: Dictionary containing updated record
        """

        return self._put("series/editor", self.ver_uri, data=data)
