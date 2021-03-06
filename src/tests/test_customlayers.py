import json

import pytest
from fastapi import status
from starlette.testclient import TestClient

from ..app.api.schemas import CustomLayer, TokenData
from ..app.utils.http import HTTPFactory
from ..app.db import customlayers as customlayers_repository
from ..app.utils.env import ACCESS_TOKEN_KEY

VALID_PAYLOAD = {
    "is_public": False,
    "layer_name": "test",
    "layer": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "coordinates": [
                        15, 15
                    ],
                    "type": "Point"
                },
                "properties": {},
                "id": "string",
                "bbox": None
            }
        ],
        "bbox": None
    }
}

VALID_PUBLIC_LAYER = {
    "user_id": 1,
    "id": 1,
    "layer_name": "test",
    "is_public": True,
    "layer": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "coordinates": [
                        15, 15
                    ],
                    "type": "Point"
                },
                "properties": {},
                "id": "string",
                "bbox": None
            }
        ],
        "bbox": None
    }
}

VALID_PRIVATE_LAYER = {
    "user_id": 1,
    "id": 2,
    "layer_name": "test",
    "is_public": False,
    "layer": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "coordinates": [
                        15, 15
                    ],
                    "type": "Point"
                },
                "properties": {},
                "id": "string",
                "bbox": None
            }
        ],
        "bbox": None
    }
}

INVALID_PAYLOAD_GEOJSON_COORDINATE = {
    "is_public": False,
    "layer_name": "test",
    "layer": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point"
                },
                "properties": {},
                "id": "string"
            }
        ]
    }
}

INVALID_PAYLOAD_GEOJSON_GEOM_TYPE = {
    "is_public": False,
    "layer_name": "test",
    "layer": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "coordinates": [
                        15, 15
                    ],
                    "type": "point"
                },
                "properties": {},
                "id": "string"
            }
        ]
    }
}


@pytest.mark.parametrize(
    "customlayer_payload, access_token,token_data, expected_status_code",
    [
        [VALID_PAYLOAD, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_201_CREATED],
        [VALID_PAYLOAD, "some-dummy-token", False, status.HTTP_401_UNAUTHORIZED],
        [INVALID_PAYLOAD_GEOJSON_GEOM_TYPE, "some-dummy-token", {"username": "john", "user_id": 1},
         status.HTTP_422_UNPROCESSABLE_ENTITY],
        [INVALID_PAYLOAD_GEOJSON_COORDINATE, "some-dummy-token", {"username": "john", "user_id": 1},
         status.HTTP_422_UNPROCESSABLE_ENTITY],
    ]
)
def test_create_layer(test_app: TestClient, monkeypatch, customlayer_payload, access_token, token_data,
                      expected_status_code):
    async def mock_check_credentials(token: str):
        if access_token:
            return token_data, access_token
        return None, None

    async def mock_create(payload: CustomLayer, user: token_data):
        return 1

    async def mock_retrieve_by_id(id: int):
        return {"id": 1, "data": json.dumps(customlayer_payload["layer"])}

    test_app.headers[ACCESS_TOKEN_KEY] = access_token
    monkeypatch.setattr(HTTPFactory.instance, "check_user_credentials", mock_check_credentials)
    monkeypatch.setattr(customlayers_repository, "create", mock_create)
    monkeypatch.setattr(customlayers_repository, "retrieve_by_id", mock_retrieve_by_id)

    response = test_app.post("/layers/", data=json.dumps(customlayer_payload))

    assert response.status_code == expected_status_code
    if response.status_code == status.HTTP_200_OK:
        assert response.json() == {"id": 1, "status": "created"}


@pytest.mark.parametrize(
    "retrieved_layer,  access_token,token_data, expected_status_code",
    [
        [VALID_PUBLIC_LAYER, "some-dummy-token", None, status.HTTP_200_OK],
        [VALID_PRIVATE_LAYER, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_200_OK],
        [VALID_PRIVATE_LAYER, "some-dummy-token", {"username": "notjohn", "user_id": 2}, status.HTTP_401_UNAUTHORIZED],
        [None, None, None, status.HTTP_401_UNAUTHORIZED],
        [None, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_404_NOT_FOUND],
    ]
)
def test_retrieve_layer(test_app: TestClient, monkeypatch, retrieved_layer, access_token, token_data,
                        expected_status_code):
    async def mock_check_credentials(token: str):
        if access_token:
            return token_data, access_token
        return None, None

    async def mock_retrieve_by_id(id: int):
        if retrieved_layer:
            return {"is_public": retrieved_layer["is_public"], "user_id": retrieved_layer["user_id"],
                    "data": json.dumps(retrieved_layer["layer"])}
        return None

    test_app.headers[ACCESS_TOKEN_KEY] = access_token
    monkeypatch.setattr(HTTPFactory.instance, "check_user_credentials", mock_check_credentials)
    monkeypatch.setattr(customlayers_repository, "retrieve_by_id", mock_retrieve_by_id)

    response = test_app.get("/layers/1")

    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "customlayer_payload, access_token,token_data, expected_status_code",
    [
        [VALID_PAYLOAD, "some-dummy-token", {"username": "john", "id": 1}, status.HTTP_204_NO_CONTENT],
        [VALID_PAYLOAD, "some-dummy-token", False, status.HTTP_401_UNAUTHORIZED],
        [INVALID_PAYLOAD_GEOJSON_GEOM_TYPE, "some-dummy-token", {"username": "john", "user_id": 1},
         status.HTTP_422_UNPROCESSABLE_ENTITY],
        [INVALID_PAYLOAD_GEOJSON_COORDINATE, "some-dummy-token", {"username": "john", "user_id": 1},
         status.HTTP_422_UNPROCESSABLE_ENTITY],
    ]
)
def test_update_layer(test_app: TestClient, monkeypatch, customlayer_payload, access_token, token_data,
                      expected_status_code):
    async def mock_check_credentials(token: str):
        if access_token:
            return token_data, access_token
        return None, None

    async def mock_retrieve_by_id(id: int):
        return {"id": 1, "user_id": 1, "data": json.dumps(customlayer_payload["layer"])}

    async def mock_update(payload, layer_id):
        return 1

    test_app.headers[ACCESS_TOKEN_KEY] = access_token
    monkeypatch.setattr(HTTPFactory.instance, "check_user_credentials", mock_check_credentials)
    monkeypatch.setattr(customlayers_repository, "update", mock_update)
    monkeypatch.setattr(customlayers_repository, "retrieve_by_id", mock_retrieve_by_id)

    response = test_app.put("/layers/1", data=json.dumps(customlayer_payload))

    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "retrieved_custom_layer,  access_token,token_data, expected_status_code",
    [
        [VALID_PUBLIC_LAYER, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_204_NO_CONTENT],
        [None, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_404_NOT_FOUND],
        [None, None, None, status.HTTP_401_UNAUTHORIZED]
    ]
)
def test_delete_layer(test_app: TestClient, monkeypatch, retrieved_custom_layer, access_token, token_data,
                      expected_status_code):
    async def mock_check_credentials(token: str):
        if access_token:
            return token_data, access_token
        return None, None

    async def mock_retrieve_by_id(id: int):
        return retrieved_custom_layer

    async def mock_delete(payload, layer_id):
        return 1

    test_app.headers[ACCESS_TOKEN_KEY] = access_token
    monkeypatch.setattr(HTTPFactory.instance, "check_user_credentials", mock_check_credentials)
    monkeypatch.setattr(customlayers_repository, "update", mock_delete)
    monkeypatch.setattr(customlayers_repository, "retrieve_by_id", mock_retrieve_by_id)
    response = test_app.delete("/layers/1")
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "retrieved_custom_layers, access_token,token_data, expected_status_code",
    [
        [[VALID_PUBLIC_LAYER, VALID_PRIVATE_LAYER], "some-dummy-token", {"username": "john", "user_id": 1},
         status.HTTP_200_OK],
        [None, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_404_NOT_FOUND],
        [None, None, None, status.HTTP_401_UNAUTHORIZED]
    ]
)
def test_retrieve_all_user_layers(test_app: TestClient, monkeypatch, retrieved_custom_layers, access_token, token_data,
                                  expected_status_code):
    async def mock_check_credentials(token: str):
        if access_token:
            return token_data, access_token
        return None, None

    async def mock_retrieve_by_user_id(id: int):
        return retrieved_custom_layers

    test_app.headers[ACCESS_TOKEN_KEY] = access_token
    monkeypatch.setattr(HTTPFactory.instance, "check_user_credentials", mock_check_credentials)
    monkeypatch.setattr(customlayers_repository, "retrieve_by_user_id", mock_retrieve_by_user_id)

    response = test_app.get("/layers/?user_id=8")
    assert response.status_code == expected_status_code
    if response.status_code == status.HTTP_200_OK:
        assert len(response.json()) == 2


@pytest.mark.parametrize(
    "user_id , access_token, token_data, expected_status_code",
    [
        [1, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_204_NO_CONTENT],
        [2, "some-dummy-token", {"username": "john", "user_id": 1}, status.HTTP_401_UNAUTHORIZED],
        [2, None, None, status.HTTP_401_UNAUTHORIZED],
    ]
)
def test_delete_all_user_layers(test_app: TestClient, monkeypatch, user_id, access_token, token_data,
                                expected_status_code):
    async def mock_check_credentials(token: str):
        if access_token:
            return token_data, access_token
        return None, None

    async def mock_delete_by_user_id(id: int):
        return True

    test_app.headers[ACCESS_TOKEN_KEY] = access_token
    monkeypatch.setattr(HTTPFactory.instance, "check_user_credentials", mock_check_credentials)
    monkeypatch.setattr(customlayers_repository, "delete_by_user_id", mock_delete_by_user_id)

    response = test_app.delete(f"/layers/?user_id={user_id}")
    assert response.status_code == expected_status_code


def test_retrieve_all_public_layer(test_app: TestClient, monkeypatch):
    async def mock_retrieve_all_public_layers():
        return [VALID_PUBLIC_LAYER]

    monkeypatch.setattr(customlayers_repository, "retrieve_all_public_layers", mock_retrieve_all_public_layers)
    response = test_app.get("/layers")
    assert response.status_code == status.HTTP_200_OK
