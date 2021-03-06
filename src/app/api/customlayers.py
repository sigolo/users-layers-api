from typing import List, Optional

from ..db import customlayers as layers_repository
from geojson_pydantic.features import FeatureCollection
from fastapi import APIRouter, status, Header, Response, Request
from .schemas import CustomLayer, CustomLayerResponse
from ..utils.Exceptions import raise_401_exception, raise_404_exception, raise_500_exception

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_item(request: Request, payload: CustomLayer, token: Optional[str] = Header(None)):
    if not request.state.user:
        raise_401_exception()
    layer_id = await layers_repository.create(payload, request.state.user)
    layer_record = await layers_repository.retrieve_by_id(layer_id)
    if not layer_record:
        raise_500_exception("Problem occurred during item creation")
    return {"id": layer_record.get("id"), "status": "created"}


@router.get("/", response_model=List[CustomLayerResponse], status_code=status.HTTP_200_OK)
async def retrieve_by_user(request: Request, user_id: Optional[int] = None, token: Optional[str] = Header(None)):
    if user_id is None:
        public_layer_records = await layers_repository.retrieve_all_public_layers()
        return public_layer_records
    if not request.state.user:
        raise_401_exception()
    layer_records = await layers_repository.retrieve_by_user_id(user_id)
    if not layer_records:
        raise_404_exception()
    return layer_records


@router.get("/{layer_id}", response_model=FeatureCollection, status_code=status.HTTP_200_OK)
async def retrieve_by_id(request: Request, layer_id: int, token: Optional[str] = Header(None)):
    layer_record = await layers_repository.retrieve_by_id(layer_id)
    if layer_record and layer_record.get("is_public"):
        return FeatureCollection.parse_raw(layer_record.get("data"))
    if not request.state.user:
        raise_401_exception()
    if not layer_record:
        raise_404_exception()
    if request.state.user["user_id"] != layer_record.get("user_id"):
        raise_401_exception()
    return FeatureCollection.parse_raw(layer_record.get("data"))


@router.put("/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_layer(request: Request, layer_id: int, payload: CustomLayer,
                       token: Optional[str] = Header(None)):
    if not request.state.user:
        raise_401_exception()
    layer_record = await layers_repository.retrieve_by_id(layer_id)
    if not layer_record:
        raise_404_exception()
    layer_id = await layers_repository.update(layer_id, payload)
    print("layer id is: ", layer_id)
    layer_record = await layers_repository.retrieve_by_id(layer_id)
    if not layer_record:
        raise_500_exception("Problem occurred during item update")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_layer(request: Request, layer_id: int, token: Optional[str] = Header(None)):
    if not request.state.user:
        raise_401_exception()
    layer_record = await layers_repository.retrieve_by_id(layer_id)
    if not layer_record:
        raise_404_exception()
    if request.state.user["user_id"] != layer_record.get("user_id"):
        raise_401_exception()
    await layers_repository.delete(layer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_layers_by_user(request: Request, user_id: int, token: Optional[str] = Header(None)):
    if not request.state.user or request.state.user["user_id"] != user_id:
        raise_401_exception()
    await layers_repository.delete_by_user_id(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
