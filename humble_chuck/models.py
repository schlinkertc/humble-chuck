# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_models.ipynb.

# %% auto 0
__all__ = ['DataModelT', 'model_dump_for_display', 'DisplayMixin', 'BaseModel', 'read_yaml_key', 'BaseSettings']

# %% ../nbs/06_models.ipynb 3
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict
import logging
from json2html import json2html
from humble_chuck.delegation import delegates
from typing import *
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import (
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource
)
from pydantic import create_model,Field
from pydantic.fields import FieldInfo
import yaml
from pathlib import Path

# %% ../nbs/06_models.ipynb 6
@delegates(PydanticBaseModel.model_dump) 
def model_dump_for_display(
    model:PydanticBaseModel, #The model to by displayed
    **kwargs
):
    """Calls PydanticBaseModel.model_dump(), 
    but if there is an issue it raises a warning and passes to allow default representation.  

    Delegates kwargs to PydanticBaseModel.model_dump
    """
    kwargs['mode']='json'
    try:
        return model.model_dump(**kwargs)
    except Exception as e:
        logging.warning(e)
        pass

# %% ../nbs/06_models.ipynb 7
class DisplayMixin:
    
    def _repr_json_(self):
        return model_dump_for_display(
            self,
            mode='json',
            **self.model_config.get('repr_kwargs', {})
        )

    def _repr_html_(self):
        return json2html.convert(
            model_dump_for_display(self, mode='json', **self.model_config.get('repr_kwargs', {}))
        )

# %% ../nbs/06_models.ipynb 9
class BaseModel(PydanticBaseModel,DisplayMixin):
    pass


# %% ../nbs/06_models.ipynb 18
def read_yaml_key(file_path: str, target_key: str) -> dict:
    """
    Reads values from a specific key in a YAML file and returns them as a dictionary.

    :param file_path: Path to the YAML file.
    :param target_key: The key whose values need to be extracted.
    :return: A dictionary containing the values for the specified key.
    """
    import yaml  # Ensure PyYAML is installed and imported

    if not file_path:
        return {}
        
    try:
        with open(file_path, 'r') as yaml_file:
            yaml_content = yaml.safe_load(yaml_file) or {}
    except FileNotFoundError:
        return {}
    
    return yaml_content.get(target_key, {})

# %% ../nbs/06_models.ipynb 20
class YMLSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source class that loads variables from a JSON file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        env_prefix = self.config.get('env_prefix')
        file_content = read_yaml_key(
            self.config.get('yml_settings_path'),
            env_prefix
        )

        field_value = file_content.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d

# %% ../nbs/06_models.ipynb 21
class BaseSettings(PydanticBaseSettings,DisplayMixin):
    model_config = SettingsConfigDict(
        yml_settings_path = Path.home() / ".humble-chuck-settings.yml"
    )

    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[PydanticBaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YMLSettingsSource(settings_cls),
            file_secret_settings,
        )

# %% ../nbs/06_models.ipynb 27
DataModelT = TypeVar('DataModelT')
