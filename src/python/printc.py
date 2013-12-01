
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


def printFieldFormat ( name, currentOffset, field, varIdex, formatString ) :

    width = 0

    if field.isFixed() :
        width = field.getType().getFixedWidth()
    
    baseDict = { "message" : name, "offset" : currentOffset, "index" : varIdex, "width" : width }

    updateFromField( baseDict, field )

    print formatString % baseDict

    return currentOffset + width


def printC ( typeDb ) :

    print HEADER

    # first go though and make us types
    # so that we can have the compiler
    # check for type error for the user.
    for name, info in typeDb.items() :

        if info.isComposite( ) :
            print "typedef struct %s_ {} %s ;" % ( name, name )
            print "static const uint64_t %s_tag = 0x%s ;" % ( name, info.getTag( ) )


    print ""

    for name, info in typeDb.items() :
        if info.isComposite( ) :
            print "struct %s_builder ;" % ( name, )

    print ""
    
    for name, info in typeDb.items() :

        if info.isComposite( ) :

            print "struct %s_builder {" % ( name, )

            varIndex      = len( info.getVar( ) ) - 1
            currentOffset = OFFSET_SIZE * len( info.getVar( ) )

            for field in info.getFields( ) :
                keys = {}

                if field.isRepeated() :
                    keys[ 'array' ] = "*"

                else :
                    keys[ 'array' ] = ""
                
                updateFromField( keys, field )

                if field.isComposite() or field.getType( ).isDynamic( ):
                    print "  struct %(typeName)s_builder*%(array)s %(field)s ;" % keys

                else :
                    print "  %(type)s %(array)s%(field)s ;" % keys
                    
                if ( not field.isFixed() ) and (
                    not (
                        ( field.isComposite() and not field.isRepeated() ) \
                        or field.getType().isDynamic( ) \
                        )) :
                    print "  size_t %(field)s_length ;" % keys
                
            print "} ;"

            print SETTER_SIG         % { "message" : name, "end" : ";" }
            print COMPUTE_LENGTH_SIG % { "message" : name, "end" : ";" }

    for name, info in typeDb.items() :

        if info.isComposite( ) :

            hasComposite = False

            print "/***** type %s *****/" % ( info.getName(), )

            varFields = info.getVar( )

            if info.isFixed() :
                print GET_FIXED_LENGTH     % { "message" : name, "width" : info.getFixedWidth( ) }
                print COMPUTE_FIXED_LENGTH % { "message" : name, "width" : info.getFixedWidth( ) }

            else :
                print GET_VAR_LENGTH % { "message" : name, "width" : info.getFixedWidth( ) }

                print COMPUTE_LENGTH_SIG % { "message" : name, "end" : "{" }

                print "    size_t length = %d ;" % ( info.getFixedWidth( ), )

                for field in varFields :

                    if field.isRepeated() :
                        print COMPUTE_REPETED_LENGTH % \
                              { 'fieldName' : field.getName( ), 'fieldType' : field.getType( ).getName( ) }                        
                    elif field.isComposite( ) or field.getType( ).isDynamic( ) :
                        print "    if ( builder->%s != NULL ) length += compute_%s_length( builder->%s ) ;" % \
                              ( field.getName( ), field.getType( ).getName( ), field.getName( ) )
                    else :
                        print "    length += builder->%s_length ; " % ( field.getName(), )

                print "    return length;\n}"

            varIndex      = len( info.getVar( ) ) - 1
            currentOffset = OFFSET_SIZE * len( info.getVar( ) )

            for field in info.getFixed( ) :
                currentOffset = printFieldFormat( name, currentOffset, field, varIndex, FIXED_GETTER )


            if len( varFields ) > 0 :
                if varFields[ 0 ].isRepeated( ) :
                    currentOffset = printFieldFormat( name, currentOffset, varFields[ 0 ], varIndex, FIRST_REPETED_GETTER )

                elif varFields[ 0 ].getType( ).isDynamic( ):
                    currentOffset = printFieldFormat( name, currentOffset, varFields[ 0 ], varIndex, FIRST_TAGGED_GETTER )

                else:
                    currentOffset = printFieldFormat( name, currentOffset, varFields[ 0 ], varIndex, FIRST_VAR_GETTER )

                varIndex -= 1

            for field in varFields[ 1 : ] :                
                if field.isRepeated( ) :
                    currentOffset = printFieldFormat( name, currentOffset, field, varIndex, REPETED_GETTER )

                elif field.getType( ).isDynamic( ):
                    currentOffset = printFieldFormat( name, currentOffset, field, varIndex, TAGGED_GETTER )
                    
                else:
                    currentOffset = printFieldFormat( name, currentOffset, field, varIndex, VAR_GETTER )
                    
                varIndex -= 1


            varIndex      = len( varFields ) - 1
            currentOffset = OFFSET_SIZE * len( varFields )

            for field in varFields :
                if field.isComposite() == True or field.getType( ).isDynamic() == True :
                    hasComposite = True #BOOG do I need this for repeted?
                    
            print SETTER_SIG % { "message" : name, "end" : "{" }

            if ( hasComposite == True ) :
                print "    size_t wrote ;"

            print "    size_t current_offset = %d ;" % ( info.getFixedWidth( ), )
            

            print FIXED_LENGTH_CHECK % ( info.getFixedWidth( ), )
    
            for field in info.getFixed( ) :
                if field.isComposite( ):
                    currentOffset = printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_COMPOSITE_FIXED )
                else:
                    currentOffset = printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_FIXED )


            if len( varFields ) > 0:

                for field in varFields :

                    if field.isRepeated( ) :
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_REPETED_VAR )

                    elif field.isComposite( ) or field.getType().isDynamic( ):
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_COMPOSITE_VAR )

                    else :
                        printFieldFormat( name, currentOffset, field, varIndex, VAR_LENGTH_CHECK )
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_VAR )

                    
                    currentOffset = printFieldFormat( name, currentOffset, field, varIndex, SET_END )
                    varIndex -= 1

            
            print "\n    return current_offset;\n}\n"

            
    print TAGGED_FIELD_BUILDER_START
    
    for name, info in typeDb.items() :

        if info.isComposite( ) :
            print TAGGED_FIELD_BUILDER_TYPE % \
                  { 'tag' : info.getTag() , 'type' : info.getName() }

    print TAGGED_FIELD_BUILDER_END



    print TAGGED_FIELD_COMPUTER_START
    
    for name, info in typeDb.items() :

        if info.isComposite( ) :
            print TAGGED_FIELD_COMPUTER_TYPE % \
                  { 'tag' : info.getTag() , 'type' : info.getName() }

    print TAGGED_FIELD_COMPUTER_END


    print FOOTER
