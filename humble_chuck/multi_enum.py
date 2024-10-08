"""A powerful solution for mapping multiple aliases to a single canonical value in Python."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_multi_enum.ipynb.

# %% auto 0
__all__ = ['MultiEnum']

# %% ../nbs/03_multi_enum.ipynb 3
from collections import defaultdict
from enum import Enum,EnumMeta
from typing import *
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue

# %% ../nbs/03_multi_enum.ipynb 6
def merge_dicts_of_tuples(*dicts,allow_duplicate_keys=True):
    """merges an arbitrary number of dictionaries with tuple values by concatenating values with the same keys."""
    out=defaultdict(tuple)
    for d in dicts:
        for k,v in d.items():
            if not allow_duplicate_keys and out.get(k):
                raise ValueError(f"{k} is duplicated")
            
            else: 
                out[k] += v
            
    return dict(out)

# %% ../nbs/03_multi_enum.ipynb 9
class MultiEnumMeta(EnumMeta):
    
    """
    Metaclass for MultiEnum, adding support for merging multiple MultiEnum objects and managing multiple aliases 
    for a single canonical value.

    Methods:
    - `__add__(cls, other)`: Combine two MultiEnum objects, merging their member mappings.  
    - `__iadd__(cls, other)`: In-place addition of MultiEnum objects, ensuring no duplicate aliases while preserving the canonical value.  
    - `__radd__(cls, other)`: Right-hand addition for merging multiple MultiEnum objects.  
    - `to_dict(cls)`: Convert the MultiEnum members into a dictionary, where each key is mapped to a tuple of canonical value and its aliases.  
    """
    
    def __add__(cls, other):
        """You can add MultiEnum objects together to return their combined `_member_map_`s """
        return merge_dicts_of_tuples(cls.to_dict(),other.to_dict(),allow_duplicate_keys=False)
    
    def __iadd__(cls, other):
        """This allows the += operator to merge two MultiEnums while preserving the order of the canonical value."""
        combined = merge_dicts_of_tuples(cls.to_dict(), other.to_dict(), allow_duplicate_keys=True)
        
        for key, values in combined.items():
            # Preserve the canonical value (the first value of the original MultiEnum)
            original_canonical_value = cls._value2member_map_[key]._value_ if key in cls._value2member_map_ else None
            
            # Deduplicate while preserving order; keep the canonical value as the first element
            seen = set()
            deduplicated_values = []
            
            # Start with the canonical value, ensuring it's the first one in the list
            if original_canonical_value:
                deduplicated_values.append(original_canonical_value)
                seen.add(original_canonical_value)

            # Add other values, excluding any duplicates
            for value in values:
                if value not in seen:
                    deduplicated_values.append(value)
                    seen.add(value)
            
            combined[key] = tuple(deduplicated_values)
        
        return combined
    
    def __radd__(cls, other):
        """This allows you to merge mulitple MultiEnums"""
        return merge_dicts_of_tuples(cls.to_dict(),other,allow_duplicate_keys=False)
    
    def to_dict(cls) -> Dict[str,Tuple]:
        return {k:v._all_values for k,v in cls._member_map_.items()}
    

# %% ../nbs/03_multi_enum.ipynb 11
class MultiEnum(Enum,metaclass=MultiEnumMeta):
    """
    A Many-to-One mapping in which none of the possible options can be mapped to more than one value. 
    
    """

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        
        obj._value_ = values[0]
        
        for other_value in set(values[1:]):

            existing_map = cls._value2member_map_.get(other_value) # this MUST be none
            if existing_map:
                # if the any of the acceptable values for the new obj already have a mapped instance,throw an error
                raise ValueError(f"{other_value} is trying to be mapped to {obj._value_}, but it has already been mapped to instance {existing_map}. You can't have the same value point to different objects.")
            cls._value2member_map_[other_value] = obj
        obj._all_values = tuple(x for x in values if x != ...)
        
        return obj
    
    def __init__(self,*args,**kwargs):
        # add the name of the object to the list of acceptable values if not already there
        if not self.__class__._value2member_map_.get(self.name):
            self.__class__._value2member_map_[self.name] = self
            self._all_values = self._all_values + (self.name,)
        super().__init__()

    def __repr__(self):
        return '<%s.%s: %s>' % (
                self.__class__.__name__,
                self._name_,
                ', '.join([repr(v) for v in self._all_values]),
        )
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Generates the Pydantic core schema for validation.
        """
        def validate(value: Any) -> MultiEnum:
            if value not in cls._value2member_map_:
                raise ValueError(f"Invalid value: {value}. Must be one of {list(cls._value2member_map_.keys())}.")
            return cls._value2member_map_[value]

        valid_values = list(cls._value2member_map_.keys())
        
        return core_schema.chain_schema([
            core_schema.literal_schema(valid_values),  # Use literal schema instead of enum
            core_schema.no_info_plain_validator_function(validate),
        ])

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Defines the JSON schema for the MultiEnum type, with detailed info about each member.
        """
        valid_values = list(cls._value2member_map_.keys())

        # Create a descriptive schema for each enum member
        enum_description: List[Dict[str, Any]] = []
        for member in cls:
            enum_description.append({
                'name': member.name,
                'canonical_value': member._value_,
                'aliases': [alias for alias in member._all_values if alias != member._value_],
            })
        
        # Generate the base JSON schema using a literal schema
        json_schema = handler(core_schema.literal_schema(valid_values))

        # Add the detailed description and the class docstring
        json_schema.update({
            'enum': valid_values,  # Ensure enum values include all canonical and alias values
            'description': cls.__doc__ or 'A custom MultiEnum type',  # Use the docstring as description
            'details': enum_description  # Include a detailed breakdown of each enum value
        })
        return json_schema
