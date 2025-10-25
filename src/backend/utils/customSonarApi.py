from typing import Any, Union

from pyarr import SonarrAPI
from pyarr.types import JsonObject
from requests import Response


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

    # DELETE /series/{id}
    def del_series(
        self,
        id_: int,
        delete_files: bool = False,
        add_import_list_exclusion: bool = False,
    ) -> Union[Response, JsonObject, dict[Any, Any]]:
        """Delete the series with the given ID

        Args:
            id_ (int): Database ID for series
            delete_files (bool, optional): If true series folder and files will be deleted. Defaults to False.

        Returns:
            dict: Blank dictionary
        """
        # File deletion does not work
        params = {
            "deleteFiles": delete_files,
            "addImportListExclusion": add_import_list_exclusion,
        }
        return self._delete(f"series/{id_}", self.ver_uri, params=params)
