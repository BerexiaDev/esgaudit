# Audit Log Library

This is a library that provides a simple way to log audit events in a database.
It is designed to be used in a Flask project and uses MongoDB as the database.
## Installation

You can install the library using pip:

```bash
pip install git+https://github.com/BerexiaDev/esgaudit.git@main
```

## Usage
AuditBlueprint is a class that is used to create an audit log blueprint. It takes the following parameters:
- **log_methods**: A list of methods to log. The default is ["GET", "POST", "PUT", "DELETE"].
```python
from audit_logger import AuditBlueprint

blueprint = AuditBlueprint(
    "ESG Audit Log Library",
    __name__,
)
```
Should store the old data in the global scope when updating or deleting a record. This is because the old data is not available after the request is completed.
```python
def save_company_profile(data):
    company_id = data.get("id", None)
    company_profile = CompanyProfile(**{"id": company_id}).load()

    # Save mode
    if not company_profile.id:
        company_profile = CompanyProfile(**{**data})
        message, status_code = "Company Profile created successfully", 201

    # Update mode
    else:
        # KEEP OLD DATA IN GLOBAL SCOPE FOR LOGGING IN AFTER REQUEST
        g.old_data = copy.deepcopy(company_profile.to_dict())

        company_profile.name = data.get("name", None)
    company_profile.save()


def delete_target_settings(target_setting_id):
    target_setting = TargetSettings(**{"id": target_setting_id}).load()

    if not target_setting.id:
        return {
            "status": "fail",
            "message": "No target found with the provided ID.",
       }, 404

    g.old_data = copy.deepcopy(target_setting.to_dict())
    target_setting.delete()
    return {
        "status": "success",
        "message": "Target deleted successfully.",
    }, 200
```

Target collection name (table name) is required to log the audit event. It is stored in the global scope as well.
Currently it is done in the Document class as it is the base class for all models.
```python
class Document:
    __TABLE__ = None
    _id = None

    def __init__(self, **kwargs):
        g.table_name = self.__TABLE__

```
You need to make sure that the correct table name is being set in the global scope.
```python
def delete_entity(id):
    entity = Entity(**{"_id": id}).load()
    if not entity.id:
        return {
            "status": "fail",
            "message": "No entity found wit the given id!",
        }, 404

    g.old_data = copy.deepcopy(entity.to_dict())

    entity.delete()

    EntityDomaine.delete_all({"entity_id": id})
    g.table_name = Entity.__TABLE__
    return {"status": "success", "message": "Entity deleted successfully!"}, 200
```