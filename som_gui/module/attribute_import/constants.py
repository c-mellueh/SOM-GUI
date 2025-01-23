EXPORT_PATH = "attribute_export"
FILETYPE = "Excel  (*.xlsx);;all (*.*)"

GUID = "GUID"
GUID_ZWC = "GUID_ZWC"
NAME = "NAME"
PROPERTY_SET = "PROPERTY_SET"
VALUE = "VALUE"
DATATYPE = "DATATYPE"
FILE = "FILE"
IFCTYPE = "IFC_TYPE"
IDENTIFIER = "IDENTIFIER"
ENTITY_TABLE_NAME = "entities"
CHECKED = "IS_CHECKED"
IS_DEFINED = "IS_DEFINED"
VALUE_TYPE = "VALUE_TYPE"
DESCRIPTION = "DESCRIPTION"
FILTER_TYPE = "FILTER_TYPE"
USE_CASE = "USE_CASE"
PHASE = "PHASE"

ENTITY_TABLE_HEADER = [GUID_ZWC,GUID,NAME,IFCTYPE,FILE,IDENTIFIER]
ENTITY_TABLE_DATATYPES = ["CHAR(64)","CHAR(64)","TEXT","TEXT","TEXT","TEXT"]

ATTRIBUTE_TABLE_NAME = "attributes"
ATTRIBUTE_TABLE_HEADER = [GUID_ZWC,GUID,PROPERTY_SET,NAME,VALUE,DATATYPE,CHECKED,IS_DEFINED]
ATTRIBUTE_TABLE_DATATYPES = ["CHAR(64)","CHAR(64)","TEXT","TEXT","TEXT","TEXT","INTEGER","INTEGER"]

SOM_TABLE_NAME = "som_attributes"
SOM_TABLE_HEADER = [GUID,PROPERTY_SET,NAME,VALUE,VALUE_TYPE,DATATYPE,IDENTIFIER]
SOM_TABLE_DATATYPES = ["CHAR(64)","TEXT","TEXT","TEXT","TEXT","TEXT","TEXT"]

FILTER_TABLE_NAME = "filters"
FILTER_TABLE_HEADER = [NAME,DESCRIPTION,FILTER_TYPE]
FILTER_TABLE_DATATYPES = ["TEXT","TEXT","TEXT"]

ATTRIBUTE_FILTER_TABLE_NAME = "attribute_filters"
ATTRIBUTE_FILTER_TABLE_HEADER = [GUID,USE_CASE,PHASE,VALUE]
ATTRIBUTE_FILTER_TABLE_DATATYPES = ["TEXT","TEXT","TEXT","INTEGER"]

FILTERED_SOM_ATTRIBUTES_TABLE_NAME = "filtered_som_attributes"