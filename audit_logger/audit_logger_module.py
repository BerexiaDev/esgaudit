from datetime import datetime

from flask import Blueprint, request, g
from audit_logger.utils import get_json_body, get_only_changed_values_and_id, get_action
from audit_logger.mongo_db import MongoDB

SUCCESS_STATUS_CODES = [200, 201, 204]
DEFAULT_LOG_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
PRIMARY_KEY_MAPPING = {
    "target_settings": "action",
    "attachments": "filename",
    "bilan_carbon": "campaign_name",
    "bilan_factor": "type_emission.large_name",
    "form_checks": "technical_check",
    "notifications": "content",
    "users": "email",
    "ref_sectors": "label",
    "group_entities": "label",
    "group_zones": "label",
    "entity_domaines": "h1"
}
AUDIT_COLLECTION_NAME = "audit"


class AuditBlueprint(Blueprint):
    """
        AuditBlueprint is a blueprint that logs changes to a collection in a MongoDB database.
    """
    def __init__(self, *args, **kwargs):
        self.log_methods = kwargs.pop("log_methods", DEFAULT_LOG_METHODS)
        self.audit_collection = None

        super(AuditBlueprint, self).__init__(*args, **kwargs)
        self.after_request(self.after_data_request)

    def _is_loggable(self, response) -> bool:
        return request.method in self.log_methods and response.status_code in SUCCESS_STATUS_CODES

    def after_data_request(self, response):
        table_name = g.get("table_name")
        endpoint = request.path

        if not table_name or table_name == AUDIT_COLLECTION_NAME or endpoint == "/":
            return response

        primary_key = PRIMARY_KEY_MAPPING.get(table_name, "name")
        primary_key_splits = primary_key.split(".")

        if self._is_loggable(response):
            old_data = g.get("old_data", None)

            if g.get("new_data"):
                new_data = g.new_data
            else:
                new_data = get_json_body(request)

            if request.method == 'DELETE':
                new_data = new_data or None
                if old_data:
                    old_data = {"_id": old_data.get("_id")}
                    primary_value = get_primary_key_value(primary_key_splits, old_data)
                    old_data["name"] = primary_value

            elif request.method == 'GET':
                new_data = old_data = None
            else:
                if g.get("new_data") is None:
                    new_data, old_data = get_only_changed_values_and_id(old_data or {}, new_data) if old_data else (new_data, old_data)

                if response.status_code == 201:
                    primary_value = get_primary_key_value(primary_key_splits, new_data)
                    new_data["name"] = primary_value


            action = get_action(request.method, response.status_code)
            self.create_log(action, endpoint, new_value=new_data, old_value=old_data)

        return response

    def get_audit_collection(self):
        if not self.audit_collection:
            self.audit_collection = MongoDB.get_collection(AUDIT_COLLECTION_NAME)

    def create_log(self, action: str, endpoint: str, new_value=None, old_value=None):
        # TODO Change this when azure ad integrated
        # user_info = g.auth_user if g.get("auth_user") else {}
        user_info = {
            "email": "dummy@email.com",
            "fullname": "Dummy Name"
        }

        audit_log = {
            "collection": g.get("table_name"),
            "action": action,
            "endpoint": endpoint,
            "user": user_info,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.utcnow()
        }
        self.get_audit_collection()
        self.audit_collection.insert_one(audit_log)
