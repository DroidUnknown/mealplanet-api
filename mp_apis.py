# add resource api
payload = {
    "name": "menu-management",
    "displayName": "Menu Management",
    "type": "module",
    "icon_uri": "",
    "scopes": [],
    "ownerManagedAccess": false,
    "uris": [
        "/menu-management"
    ],
    "attributes": {}
}
url = "https://nonprod-keycloak.mealplanet.com/auth/admin/realms/Istio/clients/4a596c9c-e5f6-45ae-aa59-a5e3e653a472/authz/resource-server/resource"

# add scope api

url = "https://nonprod-keycloak.mealplanet.com/auth/admin/realms/Istio/clients/4a596c9c-e5f6-45ae-aa59-a5e3e653a472/authz/resource-server/scope"

payload = {
    "name": "brand-profile:healthy-cup",
    "displayName": "",
    "iconUri": ""
}

# add role policy api

url = "https://nonprod-keycloak.mealplanet.com/auth/admin/realms/Istio/clients/4a596c9c-e5f6-45ae-aa59-a5e3e653a472/authz/resource-server/policy/role"
payload = {
    "roles": [
        {
            "id": "95069dac-6dfa-42a6-bcac-24b6bfd34be1",
            "required": true
        }
    ],
    "logic": "POSITIVE",
    "name": "member",
    "description": ""
}

# add permission api scope based

url = "https://nonprod-keycloak.mealplanet.com/auth/admin/realms/Istio/clients/4a596c9c-e5f6-45ae-aa59-a5e3e653a472/authz/resource-server/permission/scope"

payload = {
    "resources": [],
    "policies": [],
    "scopes": [
        "4e74494e-9b67-4496-ad70-dbf563c9ab73",
        "44723705-406d-4d51-8dc3-87f51ea5ca40"
    ],
    "name": "all:*:brand-management:member",
    "description": "",
    "decisionStrategy": "UNANIMOUS"
}

# add permission api resource based

url = "https://nonprod-keycloak.mealplanet.com/auth/admin/realms/Istio/clients/4a596c9c-e5f6-45ae-aa59-a5e3e653a472/authz/resource-server/permission/resource"

payload = {
    "resources": [
        "c5fa3940-849f-4729-888b-3288d76de5e7"
    ],
    "policies": [
        "1daa37b2-2e15-4227-9473-db5688731e04"
    ],
    "name": "all:brand-management:admin",
    "description": "",
    "decisionStrategy": "UNANIMOUS"
}