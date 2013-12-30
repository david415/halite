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



def getFieldDict( name, currentOffset, field, varIndex ):
    baseDict            = {}
    baseDict['message'] = name
    baseDict['offset']  = currentOffset
    baseDict['index']   = varIndex
    baseDict['width']   = 0

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

    if field.isFixed() :
        baseDict['width'] = field.getType().getFixedWidth()

    return baseDict


def printC2 ( typeDb, mustacheFile = None ) :
    renderer    = pystache.Renderer()
    stache_data = getHaliteMustache(typeDb)
    print renderer.render_path(mustacheFile, stache_data)


def getHaliteMustache ( typeDb ) :
    stache_data = {}

    stache_data['types'] = getTypes( typeDb )

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

