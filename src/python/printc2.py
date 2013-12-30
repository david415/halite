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

    if field.isRepeated() :
        baseDict['is_repeated'] = True

    elif field.isComposite( ) or field.getType( ).isDynamic( ) :
        baseDict['is_composite'] = True

    else :
        baseDict['is_plane'] = True

    if field.getType( ).isDynamic( ) :
        baseDict['is_tagged'] = True

    if field.isFixed( ) == True :
        baseDict['is_fixed'] = True


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


def printC2 ( typeDb, mustacheFile = None ) :
    renderer    = pystache.Renderer()
    stache_data = getHaliteMustache(typeDb)
    print renderer.render_path(mustacheFile, stache_data)


def getHaliteMustache ( typeDb ) :
    stache_data       = {}


    stache_data['type_function_sets'] = getTypeFunctions(typeDb)
    stache_data['types'] = getTypes( typeDb )
    
    stache_data['tagged_field_builder_types'] = []

    for name, info in typeDb.items() :
        if info.isComposite( ) :
            stache_data['tagged_field_builder_types'].append({ 'tag' : info.getTag() , 'type' : info.getName() })


    stache_data['tagged_field_computer_types'] = []
    for name, info in typeDb.items() :
        if info.isComposite( ) :
            stache_data['tagged_field_computer_types'].append({ 'tag' : info.getTag() , 'type' : info.getName() })

    return stache_data



def getTypes ( typeDb ) :
    
    type_function_sets = []

    for name, info in typeDb.items() :
        
        if not info.isComposite( ) :
            continue

        type_function_set = {}

        type_function_set['has_composite'] = False
        type_function_set['message']       = info.getName()
        type_function_set['width']         = info.getFixedWidth( )
        type_function_set['tag']           = info.getTag( )

        varFields = info.getVar( )

        if info.isFixed() :
            type_function_set['is_fixed'] = True
            
        else :
            type_function_set['is_fixed'] = False

        fields = []


        varIndex      = len( info.getVar( ) ) - 1
        currentOffset = OFFSET_SIZE * len( info.getVar( ) )

        foundFirst = False
        
        for field in info.getFields( ) :
            fieldInfo = getFieldDict( name, currentOffset, field, varIndex )
            isFixed   = field.isFixed( )

            if isFixed == False :
                varIndex -= 1

            if isFixed == False and  foundFirst == False :
                fieldInfo[ 'is_first' ] = True
                foundFirst = True
            else :
                fieldInfo[ 'is_first' ] = False


            if ( field.isComposite() == True and not field.isFixed() ) or field.getType( ).isDynamic() == True :
                # BUG: do I need this for repeated?
                type_function_set['has_composite'] = True


            currentOffset += fieldInfo[ 'width' ]

            fields.append( fieldInfo )


        type_function_set[ 'fields' ] =  fields
        type_function_sets.append( type_function_set )
        
    return type_function_sets


def getTypeFunctions(typeDb):
    
    type_function_sets = []

    for name, info in typeDb.items() :
        if not info.isComposite( ) :
            continue

        type_function_set = {}

        type_function_set['has_composite'] = False
        type_function_set['message']       = info.getName()
        type_function_set['width']         = info.getFixedWidth( )
        type_function_set[ "tag" ]         = info.getTag( )

        varFields = info.getVar( )

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
                varField['type']    = field.getType( ).getName( )

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
            fieldInfo = getFieldDict(name, currentOffset, varFields[ 0 ], varIndex)
            if varFields[ 0 ].isRepeated( ) :
                type_function_set['first_repeated_getter'] = fieldInfo

            elif varFields[ 0 ].getType( ).isDynamic( ):
                type_function_set['first_tagged_getter'] = fieldInfo

            else:
                type_function_set['first_var_getter'] = fieldInfo
                
            currentOffset += fieldInfo['width']

            varIndex -= 1

        type_function_set['repeated_getter'] = []
        type_function_set['tagged_getter']   = []
        type_function_set['var_getter']      = []
        
        for field in varFields[ 1 : ] :                
            fieldInfo = getFieldDict(name, currentOffset, field, varIndex)

            if field.isRepeated( ) :
                type_function_set['repeated_getter'].append( fieldInfo )

            elif field.getType( ).isDynamic( ):
                type_function_set['tagged_getter'].append( fieldInfo )

            else:
                type_function_set['var_getter'].append( fieldInfo )

            currentOffset += fieldInfo['width']

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
            fieldInfo = getFieldDict( name, currentOffset, field, varIndex )

            if field.isComposite( ):
                type_function_set['set_field_composite_fixed'].append( fieldInfo )
            else:
                type_function_set['set_field_fixed'].append( fieldInfo )

            currentOffset += fieldInfo['width']

        type_function_set['set_field_repeated_var']  = []
        type_function_set['set_field_composite_var'] = []
        type_function_set['set_field_var']           = []
        type_function_set['set_end']                 = []
        
        if len( varFields ) > 0:
            for field in varFields :
                fieldInfo = getFieldDict( name, currentOffset, field, varIndex )

                if field.isRepeated( ) :
                    type_function_set['set_field_repeated_var'].append( fieldInfo )
                
                elif field.isComposite( ) or field.getType().isDynamic( ):
                    type_function_set['set_field_composite_var'].append( fieldInfo )

                else :
                    type_function_set['set_field_var'].append( fieldInfo )

                type_function_set['set_end'].append( fieldInfo )

                currentOffset += fieldInfo['width']
                varIndex -= 1

        type_function_sets.append(type_function_set)

    return type_function_sets



