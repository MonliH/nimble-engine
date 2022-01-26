from __future__ import annotations
from ctypes import Union
from typing import Any, List

from pyrr import Vector3

from nimble.objects import Geometry, Model3D, Scene, Material, Component
from nimble.objects import component, geometry, model_2d
from nimble.objects.model_2d import Model2D


def to_jsonable(vec: Vector3) -> List[float]:
    return list(float(v) for v in vec)


def serialize_scene(scene: Scene) -> Any:
    return {
        "objects": {
            name: serialize_model(model) for name, model in scene.objects.items()
        },
        "objects_list": scene.objects_list,
        "active_idx": scene.active_idx,
    }


def serialize_model(model: Union[Model2D, Model3D]) -> Any:
    if isinstance(model, Model2D):
        return serialize_model_2d(model)
    else:
        return serialize_model_3d(model)


def serialize_model_2d(model: Model2D) -> Any:
    return {
        "name": model.name,
        "position": to_jsonable(model.position),
        "components": [
            serialize_component(component) for component in model.components
        ],
        "base_type": "Model2D",
        "type": type(model).__name__,
        "kwargs": {
            k: v if not isinstance(v, Vector3) else to_jsonable(v)
            for k, v in geometry.kwargs.items()
        },
    }


def serialize_model_3d(model: Model3D) -> Any:
    return {
        "material": serialize_material(model.material),
        "name": model.name,
        "rotation": to_jsonable(model.rotation),
        "position": to_jsonable(model.position),
        "scale": to_jsonable(model.scale),
        "geometry": serialize_geometry(model.geometry),
        "components": [
            serialize_component(component) for component in model.components
        ],
        "base_type": "Model3D",
    }


def serialize_material(material: Material) -> Any:
    return {
        "shader": material.shader_name,
        "material_params": material.params,
    }


def serialize_component(component: Component) -> Any:
    return {
        "class_name": type(component).__name__,
        "component_id": component._id,
        "slot_values": [slot.get_jsonable() for slot in component.slots()],
    }


def serialize_geometry(geometry: Geometry) -> Any:
    return {
        "class_name": type(geometry).__name__,
        "kwargs": {
            k: v if not isinstance(v, Vector3) else to_jsonable(v)
            for k, v in geometry.kwargs.items()
        },
    }


def unserialize_scene(data: Any) -> Scene:
    scene = Scene()
    scene.objects = {
        name: unserialize_model_3d(model) for name, model in data["objects"].items()
    }
    scene.objects_list = data["objects_list"]
    scene.active_idx = data["active_idx"]
    return scene


def unserialize_model_3d(data: Any) -> Model3D:
    model = Model3D(
        unserialize_material(data["material"]),
        geometry=unserialize_geometry(data["geometry"]),
        name=data["name"],
        rotation=Vector3(data["rotation"], dtype="f4"),
        position=Vector3(data["position"], dtype="f4"),
        scale=Vector3(data["scale"], dtype="f4"),
    )
    for component in data["components"]:
        model.add_component(unserialize_component(component, model))
    return model


def unserialize_model_2d(data: Any) -> Model2D:
    model = getattr(model_2d, data["type"])(
        name=data["name"],
        position=Vector3(data["position"], dtype="f4"),
        **data["kwargs"],
    )
    for component in data["components"]:
        model.add_component(unserialize_component(component, model))
    return model


def unserialize_model(data: Any) -> Union[Model2D, Model3D]:
    if data["base_type"] == "Model2D":
        return unserialize_model_2d(data)
    else:
        return unserialize_model_3d(data)


def unserialize_material(data: Any) -> Material:
    return Material(
        data["shader"],
        **data["material_params"],
    )


def unserialize_component(data: Any, model: Model3D) -> Component:
    component_class = getattr(
        component,
        data["class_name"],
    )

    c = component_class(
        model=model,
        _id=data["component_id"],
        slot_params=data["slot_values"],
    )
    return c


def unserialize_geometry(data: Any) -> Geometry:
    geometry_class = getattr(
        geometry,
        data["class_name"],
    )
    return geometry_class(**data["kwargs"])
