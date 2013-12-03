
OFFSET_SIZE = 4


FIXED_GETTER = """
static inline %(type)s %(message)s_read_%(field)s ( %(message)s* data ) {
    return %(use)s(%(type)s%(use)s)( ((char*)data) + %(offset)d ) ;
}

static inline size_t %(message)s_length_%(field)s ( %(message)s* data ) {
    return %(width)d;
}

static inline size_t %(message)s_end_%(field)s ( %(message)s* data ) {
    return %(offset)d + %(width)d;
}

""" 

FIRST_VAR_GETTER = """
static inline size_t %(message)s_end_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] );
}

static inline %(type)s %(message)s_read_%(field)s ( %(message)s* data ) {
    size_t message_length = %(message)s_length( data ) ;
    size_t field_end      = %(message)s_end_%(field)s( data ) ;

    if ( field_end > message_length )
        return NULL ;

    return %(use)s(%(type)s%(use)s)( ((char*)data) + %(offset)d ) ;
}

static inline size_t %(message)s_length_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] - %(offset)d );
}
""" 

# repeted format <uint32_t count><uint32_t[] ends><data...>
FIRST_REPETED_GETTER = """
static inline size_t %(message)s_end_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t   message_length = %(message)s_length( data ) ;
    uint32_t count          = *(uint32_t*)( ((char*)data) + %(offset)d ) ;

    if ( index >= count )
        return 0 ;

    if ( ( %(offset)d + ( index * sizeof( uint32_t ) ) + sizeof( uint32_t ) ) > message_length )
        return 0 ;
        
    return (size_t)( ((uint32_t*)(((char*)data) + %(offset)d ))[ index ] ) ;
}


static inline size_t %(message)s_start_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t   result ;
    size_t   message_length = %(message)s_length( data ) ;
    uint32_t count          = *(uint32_t*)( ((char*)data) + %(offset)d ) ;

    if ( index >= count )
        return 0 ;

    if ( ( %(offset)d + ( index * sizeof( uint32_t ) ) + sizeof( uint32_t ) ) > message_length )
        return 0 ;

    if ( index == 0 )
        result = %(offset)d + sizeof( uint32_t ) + ( sizeof( uint32_t ) * count ) ;

    else
        result = ((uint32_t*)(((char*)data) + %(offset)d ))[ index - 1 ] ;

    return result ;
}


static inline %(type)s %(message)s_read_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t message_length = %(message)s_length( data ) ;
    size_t field_end      = %(message)s_end_%(field)s( data, index ) ;
    size_t field_start    = %(message)s_start_%(field)s( data, index ) ;

    if ( (field_end > message_length) || (field_start == 0) || (field_end == 0) )
        return NULL ;

   return %(use)s(%(type)s%(use)s)( ((char*)data) + field_start ) ;
}


static inline size_t %(message)s_length_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t field_end   = %(message)s_end_%(field)s( data, index ) ;
    size_t field_start = %(message)s_start_%(field)s( data, index ) ;

    if ( field_start == 0 || field_end == 0 )
        return 0 ;

    return field_end - field_start ;
}
"""



FIRST_TAGGED_GETTER = """
static inline size_t %(message)s_end_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] );
}


static inline char* %(message)s_read_%(field)s ( %(message)s* data ) {
    size_t message_length = %(message)s_length( data ) ;
    size_t field_end      = %(message)s_end_%(field)s( data ) ;

    if ( field_end > message_length )
        return NULL ;

    return  ((char*)data) + %(offset)d + sizeof( uint64_t ) ;
}


static inline uint64_t %(message)s_readTag_%(field)s ( %(message)s* data ) {
    return *(uint64_t*)( ((char*)data) + %(offset)d ) ;
}


static inline size_t %(message)s_length_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] - %(offset)d );
}
"""

VAR_GETTER = """
static inline size_t %(message)s_end_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] );
}

static inline %(type)s %(message)s_read_%(field)s ( %(message)s* data ) {
    size_t message_length = %(message)s_length( data ) ;
    size_t field_end      = %(message)s_end_%(field)s( data ) ;

    if ( field_end > message_length )
        return NULL ;

    return %(use)s(%(type)s%(use)s)( ((char*)data) + ((uint32_t*)data)[ %(index)d + 1 ]  ) ;
}

static inline size_t %(message)s_length_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] - ((uint32_t*)data)[ %(index)d + 1 ] );
}
""" 

# repeted format <uint32_t count><uint32_t[] ends><data...>
REPETED_GETTER = """
static inline size_t %(message)s_end_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t   message_length = %(message)s_length( data ) ;
    uint32_t field_start    = ((uint32_t*)data)[ %(index)d + 1 ] ;
    uint32_t count          = *(uint32_t*)( ((char*)data) + field_start ) ;

    if ( index >= count )
        return 0 ;

    if ( ( field_start + ( index * sizeof( uint32_t ) ) + sizeof( uint32_t ) ) > message_length )
        return 0 ;
        
    return (size_t)( ((uint32_t*)(((char*)data) + field_start ))[ index ] ) ;
}


static inline size_t %(message)s_start_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t   result ;
    size_t   message_length = %(message)s_length( data ) ;
    uint32_t field_start    = ((uint32_t*)data)[ %(index)d + 1 ] ;
    uint32_t count          = *(uint32_t*)( ((char*)data) + field_start ) ;

    if ( index >= count )
        return 0 ;

    if ( ( field_start + ( index * sizeof( uint32_t ) ) + sizeof( uint32_t ) ) > message_length )
        return 0 ;


    if ( index == 0 )
        result = field_start + sizeof( uint32_t ) + ( sizeof( uint32_t ) * count ) ;

    else
        result = ((uint32_t*)(((char*)data) + field_start ))[ index - 1 ] ;

    return result ;
}


static inline %(type)s %(message)s_read_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t message_length = %(message)s_length( data ) ;
    size_t field_end      = %(message)s_end_%(field)s( data, index ) ;
    size_t field_start    = %(message)s_start_%(field)s( data, index ) ;

    if ( field_end > message_length || field_start == 0 || field_end == 0 )
        return NULL ;

   return %(use)s(%(type)s%(use)s)( ((char*)data) + field_start ) ;
}


static inline size_t %(message)s_length_%(field)s ( %(message)s* data, uint32_t index ) {
    size_t field_end   = %(message)s_end_%(field)s( data, index ) ;
    size_t field_start = %(message)s_start_%(field)s( data, index ) ;

    if ( field_start == 0 || field_end == 0 )
        return 0 ;

    return field_end - field_start ;
}
"""

TAGGED_GETTER = """
static inline size_t %(message)s_end_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] );
}

static inline char* %(message)s_read_%(field)s ( %(message)s* data ) {
    size_t message_length = %(message)s_length( data ) ;
    size_t field_end      = %(message)s_end_%(field)s( data ) ;

    if ( field_end > message_length )
        return NULL ;

    return ((char*)data) + sizeof(uint64_t) + ((uint32_t*)data)[ %(index)d + 1 ] ;
}

static inline uint64_t %(message)s_readTag_%(field)s ( %(message)s* data ) {
    return *(uint64_t*)( ((char*)data) + ((uint32_t*)data)[ %(index)d + 1 ] );
}

static inline size_t %(message)s_length_%(field)s ( %(message)s* data ) {
    return (size_t)( ((uint32_t*)data)[ %(index)d ] - ((uint32_t*)data)[ %(index)d + 1 ] );
}
""" 

SETTER_SIG = """
static inline size_t build_%(message)s ( char* data, size_t length, struct %(message)s_builder* builder_data ) %(end)s
"""

FIXED_LENGTH_CHECK = """
    if ( length < %d )
        return 0 ;
"""

SET_FIELD_FIXED = "    memcpy( data + %(offset)d, (char*)%(take)sbuilder_data->%(field)s, %(width)d ) ;"


SET_FIELD_COMPOSITE_FIXED = """
    build_%(typeName)s( data + %(offset)d,  length - %(offset)d, builder_data->%(field)s ) ;
"""


VAR_LENGTH_CHECK = """
    if ( length < current_offset + builder_data->%(field)s_length )
        return 0 ;"""

SET_FIELD_VAR = """
    memcpy( data + current_offset, (char*)builder_data->%(field)s, builder_data->%(field)s_length ) ;
    
    current_offset += builder_data->%(field)s_length ;
"""

SET_FIELD_REPETED_VAR = """
    {
        size_t field_count = builder_data->%(field)s_length ;

        struct %(typeName)s_builder** %(field)s = builder_data->%(field)s ;

        uint32_t* offset_array = (uint32_t*)( data + current_offset + sizeof( uint32_t ) ) ;

        current_offset = sizeof( uint32_t ) * ( field_count + 1 ) ;

        for ( int i = 0 ; i < field_count ; i ++ ) {

            if ( %(field)s[i] == NULL )
                return 0 ;

            else {
                wrote = build_%(typeName)s( data + current_offset,  length - current_offset, %(field)s[i] ) ;

                if ( wrote == 0 )
                    return 0 ;

                current_offset += wrote ;

                offset_array[ i ] = current_offset ;
            }
        }
    }
"""


SET_FIELD_COMPOSITE_VAR = """
    if ( builder_data->%(field)s == NULL )
        return 0 ;

    else {
        wrote = build_%(typeName)s( data + current_offset,  length - current_offset, builder_data->%(field)s ) ;

        if ( wrote == 0 )
            return 0 ;

        current_offset += wrote ;
    }
"""

SET_END = "    ((uint32_t*)data)[ %(index)d ] = current_offset ;"

COMPUTE_LENGTH_SIG = "size_t static inline compute_%(message)s_length ( struct %(message)s_builder* builder ) %(end)s\n"


COMPUTE_FIXED_LENGTH = """
size_t static inline compute_%(message)s_length ( struct %(message)s_builder* builder ) {
    return %(width)d ;
}
"""

COMPUTE_REPETED_LENGTH = """
    size_t %(fieldName)s_length = builder->%(fieldName)s_length ;

    for ( int i = 0 ; i < %(fieldName)s_length ; i++ ) {
        if ( builder->%(fieldName)s[i] != NULL )
            length += compute_%(fieldType)s_length( builder->%(fieldName)s[i] ) ;
    }
"""

GET_FIXED_LENGTH = """
size_t static inline %(message)s_length ( %(message)s* data ) {
    return %(width)d ;
}
"""

GET_VAR_LENGTH = """
size_t static inline %(message)s_length ( %(message)s* data ) {
    return (size_t)((uint32_t*)data)[ 0 ] ;
}
"""



HEADER = """
#ifndef MESSAGE_IMPLMENTATION_H
#define MESSAGE_IMPLMENTATION_H

#include <stdint.h>
#include <string.h>

struct TaggedField_builder { uint64_t tag ; char* data ; } ;

static inline size_t build_TaggedField ( char* data, size_t length, struct TaggedField_builder* builder_data ) ;

size_t static inline compute_TaggedField_length ( struct TaggedField_builder* builder ) ;
"""

FOOTER = """
#endif /* MESSAGE_IMPLMENTATION_H  */
"""


TAGGED_FIELD_BUILDER_START = """
static inline size_t build_TaggedField ( char* data, size_t length, struct TaggedField_builder* builder_data ) {

    if ( length < 8 )
        return 0 ;

    size_t wrote ;

    memcpy( data, (char*)&builder_data->tag, sizeof( uint64_t ) ) ;

    switch( builder_data->tag ) {"""

TAGGED_FIELD_BUILDER_TYPE = """
       case 0x%(tag)s :
           wrote = build_%(type)s( data + sizeof( uint64_t ),  length - sizeof( uint64_t ), (struct %(type)s_builder*)builder_data->data ) ;
           break ;"""

TAGGED_FIELD_BUILDER_END = """
       default:
           wrote = 0 ;
           break ;
   }

   if ( wrote > 0 )
       wrote += sizeof( uint64_t ) ;

   return wrote ;
}
"""

TAGGED_FIELD_COMPUTER_START = """
size_t static inline compute_TaggedField_length ( struct TaggedField_builder* builder_data ) {

    size_t length ;

    switch( builder_data->tag ) {"""

TAGGED_FIELD_COMPUTER_TYPE = """
       case 0x%(tag)s :
           length = compute_%(type)s_length( (struct %(type)s_builder*)builder_data->data ) ;
           break ;"""

TAGGED_FIELD_COMPUTER_END = """
       default:
           length = 0 ;
           break ;
   }

   if ( length > 0 )
       length += sizeof( uint64_t ) ;

   return length ;
}
"""


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


import pystache

def printC ( typeDb ) :
    renderer = pystache.Renderer()

    stache_data = {
        'header': HEADER
        }

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

        if len(composite_builder_struct) > 0:
            composite_builder_structs.append(composite_builder_struct)

    stache_data['composite_builder_structs'] = {'structs':composite_builder_structs}

    stache_data['type_functions'] = getTypeFunctions(typeDb)

    print renderer.render_path('/home/dawuud/projects/halite-bitbucket-david415/src/messages/halite-c.mustache', stache_data)



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
            if field.isComposit() == True or field.getType( ).isDynamic() == True :
                type_function_set['has_composite'] = True #BOOG do I need this for repeted?








        type_function_sets.append(type_function_set)

    # DEBUG
    #import json
    #print "\n\n"
    #print json.dumps(type_function_sets, indent=2)
    #print "\n\n"

    return type_function_sets


