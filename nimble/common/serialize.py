from __future__ import annotations
from typing import TYPE_CHECKING, Any, List

from pyrr import Vector3

from nimble.objects.geometry import Geometry
from nimble.objects.model import Model
from nimble.objects.scene import Scene
from nimble.objects.material import Material
from nimble.objects.component import Component
from nimble.objects import component, geometry


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


def serialize_model(model: Model) -> Any:
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
        name: unserialize_model(model) for name, model in data["objects"].items()
    }
    scene.objects_list = data["objects_list"]
    scene.active_idx = data["active_idx"]
    return scene


def unserialize_model(data: Any) -> Model:
    model = Model(
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


def unserialize_material(data: Any) -> Material:
    return Material(
        data["shader"],
        **data["material_params"],
    )


def unserialize_component(data: Any, model: Model) -> Component:
    component_class = getattr(
        component,
        data["class_name"],
    )

    print(component_class)
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
