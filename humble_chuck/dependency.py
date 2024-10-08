"""Using Pydantic's `validate_call` arguments to run dependant functions"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_dependency.ipynb.

# %% auto 0
__all__ = ['logger', 'Dependency', 'depends_on']

# %% ../nbs/02_dependency.ipynb 3
import logging
from typing import Any, Callable, Dict
from pydantic import ValidationError, validate_call,GetCoreSchemaHandler
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue,GetJsonSchemaHandler

# %% ../nbs/02_dependency.ipynb 4
# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# %% ../nbs/02_dependency.ipynb 5
logger = logging.getLogger(__name__)

class Dependency:
    depends_on: Dict[str, Callable]

    @classmethod
    def validate(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the input dictionary based on the functions in `depends_on`.
        If a function is not present in the dictionary, call the function and store the result.
        """
        for key, func in cls.depends_on.items():
            if key not in value:
                logger.info(f"validating: {func.__name__} as {key}")
                output = func(value)
                value[key] = output

            else:
                logger.info(f"retrieving {key} from state.")
        return value

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Core schema definition for Pydantic, integrating the Dependency class
        with the list of functions passed via depends_on.
        """
        return core_schema.chain_schema([
            core_schema.dict_schema(),
            core_schema.no_info_plain_validator_function(cls.validate)
        ])

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Defines how the `Dependency` object should be serialized in JSON schemas.
        """
        json_schema = handler(core_schema.dict_schema())
        print(cls.depends_on)
        json_schema.update({'description': 'A custom Dependency type with named keys'})
        return json_schema


# Custom `depends_on` to parameterize the Dependency class with named keys
def depends_on(**functions: Callable) -> type:
    """
    Dynamically creates a new subclass of Dependency with the depends_on dict set to the given functions.
    This allows for named dependencies.
    """
    return type(
        f'Dependency({", ".join(f"{k}={v.__name__}" for k, v in functions.items())})',
        (Dependency,),
        {'depends_on': functions}
    )
