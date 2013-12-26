#!/usr/bin/env python

import pystache


OFFSET_SIZE = 4

def error ( message ):
    print message
    sys.exit( 1 )



typeNameToC = {
    "uint8"  : "uint8_t"      ,
    "int8"   : "int8_t"       ,
    "uint16" : "uint16_t"     ,
    "int16"  : "uint16_t"     ,
    "uint32" : "uint32_t"     ,
    "int32"  : "int32_t"      ,
    "uint64" : "uint64_t"     ,
    "int64"  : "int64_t"      ,
    "float32": "float"        ,
    "float64": "double"       ,
    }


fixedArrayTypes = {
    "sha256" : "uint8_t" ,
    "bit192" : "uint8_t" ,
    "bit256" : "uint8_t" ,
    "bit512" : "uint8_t" ,
    }

varCTypes = {
    "cstring": "char"         ,
    "bytes"  : "char"         ,
    "utf8"   : "char"         ,
    }

def updateFromField ( baseDict, field ) :
    dataType = field.getType()
    typeName = dataType.getName()
    ctype    = None
    use      = None
    take     = None

    if typeName in fixedArrayTypes :
        ctype = fixedArrayTypes[ typeName ] + "*"
        use   = ""
        take  = ""

    elif typeName in varCTypes :
        ctype = varCTypes[ typeName ] + "*"
        use   = ""
        take  = ""
        
    elif typeName in typeNameToC :
        ctype = typeNameToC[ typeName ]
        use   = "*"
        take  = "&"

    else :
        ctype = typeName + "*"
        use   = ""
        take  = ""

    baseDict[ "typeName" ] = typeName
    baseDict[ "type"     ] = ctype
    baseDict[ "use"      ] = use
    baseDict[ "take"     ] = take
    baseDict[ "field"    ] = field.getName()


def getFieldDict( name, currentOffset, field, varIndex ):
    baseDict            = {}
    baseDict['message'] = name
    baseDict['offset']  = currentOffset
    baseDict['index']   = varIndex
    baseDict['width']   = 0
    updateFromField( baseDict, field )
    if field.isFixed() :
        baseDict['width'] = field.getType().getFixedWidth()
    return baseDict

def printFieldFormat ( name, currentOffset, field, varIdex, formatString ) :

    width = 0

    if field.isFixed() :
        width = field.getType().getFixedWidth()
    
    baseDict = { "message" : name, "offset" : currentOffset, "index" : varIdex, "width" : width }

    updateFromField( baseDict, field )

    print formatString % baseDict

    return currentOffset + width

def printC2 ( typeDb, mustacheFile = None ) :
    renderer    = pystache.Renderer()
    stache_data = getHaliteMustache(typeDb)
    print renderer.render_path(mustacheFile, stache_data)

def getHaliteMustache ( typeDb ) :
    stache_data       = {}
    composite_typedef = []

    for name, info in typeDb.items() :
        if info.isComposite( ) :
            composite_typedef.append( { "name": name, "tag" : info.getTag( ) } )

    stache_data['composite_typedef'] = composite_typedef

    composite_struct_def = []

    for name, info in typeDb.items() :
        if info.isComposite( ) :
            composite_struct_def.append( { "name" : name } )

    stache_data['composite_struct_def'] = composite_struct_def

    composite_builder_structs = []

    for name, info in typeDb.items() :

        composite_builder_struct = None

        if info.isComposite( ) :
            composite_builder_struct  = {}
            composite_builder_struct['name']  = name
            varIndex      = len( info.getVar( ) ) - 1
            currentOffset = OFFSET_SIZE * len( info.getVar( ) )

            fields = []

            for field in info.getFields( ) :
                keys          = {}
                struct_field = {}

                if field.isRepeated() :
                    struct_field[ 'array' ] = "*"
                else :
                    struct_field[ 'array' ] = ""

                updateFromField( keys, field )
                struct_field['field'] = keys['field']

                if field.isComposite() or field.getType( ).isDynamic( ):
                    struct_field['is_composite'] = True
                    struct_field['typeName']     = keys['typeName']
                else:
                    struct_field['type']          = keys['type']
                if ( not field.isFixed() ) and (
                    not (
                        ( field.isComposite() and not field.isRepeated() ) \
                        or field.getType().isDynamic( ) \
                        )) :
                        struct_field['has_length'] = True

                fields.append(struct_field)

            composite_builder_struct['struct_fields']   = fields
            composite_builder_struct['setter_sig_name'] = name

        if composite_builder_struct is not None :
            composite_builder_structs.append(composite_builder_struct)

    stache_data['composite_builder_structs'] = {'structs':composite_builder_structs}

    stache_data['type_function_sets'] = getTypeFunctions(typeDb)
        
    stache_data['tagged_field_builder_types'] = []

    for name, info in typeDb.items() :
        if info.isComposite( ) :
            stache_data['tagged_field_builder_types'].append({ 'tag' : info.getTag() , 'type' : info.getName() })


    stache_data['tagged_field_computer_types'] = []
    for name, info in typeDb.items() :
        if info.isComposite( ) :
            stache_data['tagged_field_computer_types'].append({ 'tag' : info.getTag() , 'type' : info.getName() })

    return stache_data


def getTypeFunctions(typeDb):
    type_function_sets = []
    for name, info in typeDb.items() :
        if not info.isComposite( ) :
            continue

        type_function_set          = {}
        type_function_set['has_composite'] = False
        type_function_set['message']  = info.getName()
        type_function_set['width'] = info.getFixedWidth( )
        varFields                  = info.getVar( )

        if info.isFixed() :
            type_function_set['is_fixed'] = True
        else:
            fields = []
            for field in varFields :
                varField = {}
                if field.isRepeated() :
                    varField['is_repeated'] = True
                elif field.isComposite( ) or field.getType( ).isDynamic( ) :
                    varField['is_composite'] = True
                else:
                    varField['default'] = True
                    varField['message'] = field.getName( )
                    varField['type'] = field.getType( ).getName( )
                    fields.append(varField)
                type_function_set['field_lengths'] = fields
        
        varIndex      = len( info.getVar( ) ) - 1
        currentOffset = OFFSET_SIZE * len( info.getVar( ) )

        fixed_getter_sets = []
        for field in info.getFixed( ) :
            fixed_getters = getFieldDict(name, currentOffset, field, varIndex)
            currentOffset = currentOffset + fixed_getters['width']
            fixed_getter_sets.append(fixed_getters)

        if len(fixed_getter_sets) > 0:
            type_function_set['fixed_getter_sets'] = fixed_getter_sets

        if len( varFields ) > 0 :
            if varFields[ 0 ].isRepeated( ) :
                type_function_set['first_repeated_getter'] = getFieldDict(name, currentOffset, varFields[ 0 ], varIndex)
                currentOffset = currentOffset + type_function_set['first_repeated_getter']['width']
            elif varFields[ 0 ].getType( ).isDynamic( ):
                type_function_set['first_tagged_getter'] = getFieldDict(name, currentOffset, varFields[ 0 ], varIndex)
                currentOffset = currentOffset + type_function_set['first_tagged_getter']['width']
            else:
                type_function_set['first_var_getter'] = getFieldDict(name, currentOffset, varFields[ 0 ], varIndex)
                currentOffset = currentOffset + type_function_set['first_var_getter']['width']
            varIndex -= 1

        for field in varFields[ 1 : ] :                
            if field.isRepeated( ) :
                type_function_set['repeated_getter'] = getFieldDict(name, currentOffset, field, varIndex)
                currentOffset += type_function_set['repeated_getter']['width']
            elif field.getType( ).isDynamic( ):
                type_function_set['tagged_getter'] = getFieldDict(name, currentOffset, field, varIndex)
                currentOffset += type_function_set['tagged_getter']['width']
            else:
                type_function_set['var_getter'] = getFieldDict(name, currentOffset, field, varIndex)
                currentOffset += type_function_set['var_getter']['width']
            varIndex -= 1

        varIndex      = len( varFields ) - 1
        currentOffset = OFFSET_SIZE * len( varFields )

        for field in varFields :
            if field.isComposite() == True or field.getType( ).isDynamic() == True :
                # BUG: do I need this for repeated?
                type_function_set['has_composite'] = True

        type_function_set['set_field_composite_fixed'] = []
        type_function_set['set_field_fixed']           = []
        
        for field in info.getFixed( ) :
            currentInfo = getFieldDict( name, currentOffset, field, varIndex )

            if field.isComposite( ):
                type_function_set['set_field_composite_fixed'].append( currentInfo )
            else:
                type_function_set['set_field_fixed'].append( currentInfo )

            currentOffset += currentInfo['width']

        if len( varFields ) > 0:
            for field in varFields :
                if field.isRepeated( ) :
                    type_function_set['set_field_repeated_var'] = getFieldDict( name, currentOffset, field, varIndex )
                    currentOffset += type_function_set['set_field_repeated_var']['width']

                elif field.isComposite( ) or field.getType().isDynamic( ):
                    type_function_set['set_field_composite_var'] = getFieldDict( name, currentOffset, field, varIndex )
                    currentOffset += type_function_set['set_field_composite_var']['width']
                else :
                    type_function_set['var_length_check'] = getFieldDict( name, currentOffset, field, varIndex )
                    currentOffset += type_function_set['var_length_check']['width']
                    type_function_set['set_field_var'] = getFieldDict( name, currentOffset, field, varIndex )
                    currentOffset += type_function_set['set_field_var']['width']

                type_function_set['set_end'] = getFieldDict( name, currentOffset, field, varIndex )
                currentOffset += type_function_set['set_end']['width']
                varIndex -= 1

        type_function_sets.append(type_function_set)

    return type_function_sets
