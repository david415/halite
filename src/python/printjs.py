
OFFSET_SIZE = 4


FIXED_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    return convexstruct.types.%(typeName)s.read( data, offset + %(offset)d, %(width)d ) ;
} ;
"""

FIXED_COMPOSIT_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var start = offset + %(offset)d ;

    if (  start + %(width)d  > data.byteLength )
        throw new Error ( 'out of bounds error' ) ;

    return new DataView ( data.buffer, data.byteOffset + start, %(width)d ) ;
} ;
"""

FIXED_LENGTH_GETTER = """
self.%(message)s_length_%(field)s = function ( data, offset ) {
    return %(width)d;
} ;
""" 


FIRST_VAR_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var endOffset   = offset + data.getUint32( offset + ( %(index)d * 4 ), true ) ;
    var readLength  = endOffset - ( offset + %(offset)d );

    return convexstruct.types.%(typeName)s.read( data, offset + %(offset)d, readLength ) ;
} ;
"""

# repeted format <uint32_t count><uint32_t[] ends><data...>
FIRST_REPETED_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset, index ) {
    var fieldCount = data.getUint32( offset + %(offset)d, true ) ;
    var end        = offset + data.getUint32( offset + %(offset)d + ( ( index + 1 ) * 4 ), true ) ;
    var start ;

    if ( index === 0 )
        start = %(offset)d + offset + ( 4 * fieldCount ) + 4 ;
    else
        start = offset + data.getUint32( offset + %(offset)d + ( index * 4 ), true ) ;

    if ( start > end || data.byteLength < end )
        throw new Error ( 'out of bounds error' ) ;


    return new DataView ( data.buffer, data.byteOffset + start, end - start ) ;
} ;

self.%(message)s_count_%(field)s = function ( data, offset ) {
    return data.getUint32( offset + %(offset)d, true ) ;
} ;

"""

FIRST_TAGGED_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var start  = offset + 8 + %(offset)d ;
    var end    = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;

    if ( start > end || data.byteLength < end )
        throw new Error ( 'out of bounds error' ) ;

    return new DataView ( data.buffer, data.byteOffset + start, end - start ) ;
} ;

self.%(message)s_readTag_%(field)s = function ( data, offset ) {

    var endOffset   = offset + data.getUint32( offset + %(index)d * 4, true ) ;
    var readLength  = endOffset - %(offset)d ;

    return convexstruct.lib.readTag( data, offset + %(offset)d, readLength ) ;
} ;
"""

FIRST_VAR_COMPOSIT_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var start = offset + %(offset)d ; 
    var end   = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;

    if ( start > end || data.byteLength < end )    
        throw new Error ( 'out of bounds error' ) ;

    return new DataView ( data.buffer, data.byteOffset + start, end - start ) ;
} ;
"""


FIRST_VAR_LENGTH_GETTER = """
self.%(message)s_length_%(field)s = function ( data, offset ) {
    var startOffset = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;

    return endOffset - %(offset)d ;
} ;
""" 

FIRST_REPETED_LENGTH_GETTER = """
self.%(message)s_length_%(field)s = function ( data, offset, index ) {

    var fieldCount = data.getUint32( offset + %(offset)d, true ) ;
    var fieldEnd   = offset + data.getUint32( offset + %(offset)d + ( index * 4 ), true ) ;
    var fieldStart ;

    if ( index === 0 )
        fieldStart = %(offset)d + offset + ( 4 * fieldCount ) + 4 ;
    else
        fieldStart = offset + data.getUint32( offset + %(offset)d + ( ( index - 1 ) * 4 ), true ) ;

    return fieldEndnd - fieldStart ;
} ;
"""


VAR_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var startOffset = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    var endOffset   = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;
    var readLength  = endOffset - startOffset ;

    return convexstruct.types.%(typeName)s.read( data, startOffset, readLength ) ;
} ;
"""

# repeted format <uint32_t count><uint32_t[] ends><data...>
REPETED_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset, index ) {
    var baseStart  = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    var fieldCount = data.getUint32( baseStart, true ) ;
    var end        = offset + data.getUint32( baseStart + ( ( index + 1 ) * 4 ), true ) ;
    var start ;

    if ( index === 0 )
        start = baseStart + ( 4 * fieldCount ) + 4 ;
    else
        start = offset + data.getUint32( baseStart + ( index  * 4 ), true ) ;

    if ( start > end || data.byteLength < end  )
        throw new Error ( 'out of bounds error' ) ;

    return new DataView ( data.buffer, data.byteOffset + start, end - start ) ;
} ;

self.%(message)s_count_%(field)s = function ( data, offset ) {
    var baseStart  = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    return data.getUint32( baseStart, true ) ;
} ;

"""

VAR_COMPOSIT_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var start = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    var end   = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;

    if ( start > end || data.byteLength < end )
        throw new Error ( 'out of bounds error' ) ;

    return new DataView ( data.buffer, data.byteOffset + start, end - start ) ;
} ;
"""


TAGGED_GETTER = """
self.%(message)s_read_%(field)s = function ( data, offset ) {
    var start = offset + 8 + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    var end   = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;

    if ( start > end || data.byteLength < end )
        throw new Error ( 'out of bounds error' ) ;

    return new DataView ( data.buffer, data.byteOffset + start, end - start ) ;

} ;


self.%(message)s_readTag_%(field)s = function ( data, offset ) {
    var startOffset = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    var endOffset   = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;
    var readLength  = endOffset - startOffset ;

    return convexstruct.lib.readTag( data, startOffset, readLength ) ;
} ;

"""


VAR_LENGTH_GETTER = """
self.%(message)s_length_%(field)s = function ( data, offset ) {
    var startOffset = offset + data.getUint32( offset + ( %(index)d + 1 ) * 4, true ) ;
    var endOffset   = offset + data.getUint32( offset + ( %(index)d     ) * 4, true ) ;

    return endOffset - startOffset ;
} ;
""" 

SETTER_START = """
self.make_%(message)s = function ( builder_data ) {

    var documentLength  = self.compute_%(message)s_length( builder_data ) ;
    var documentBuffer  = new ArrayBuffer ( documentLength ) ;
    var documentView    = new DataView ( documentBuffer ) ;

    var wrote = self.build_%(message)s( documentView, 0, documentLength, builder_data ) ;

    if ( wrote !== documentLength )
       throw new Error ( 'wrote did not match expected length. Got ' + wrote + ' expected ' + documentLength ) ;

    return documentView ;
} ;

self.build_%(message)s = function ( data, offset, length, builder_data ) {
"""

FIXED_LENGTH_CHECK = """
    if ( length < %d  )
        return 0 ;
"""

SET_FIELD_FIXED = "    convexstruct.types.%(typeName)s.write( data, offset + %(offset)d, builder_data.%(field)s ) ;"


VAR_LENGTH_CHECK = """
    if ( length < current_offset + builder_data.%(field)s.length )
        return 0 ;"""

SET_FIELD_VAR = """
    current_offset += convexstruct.types.%(typeName)s.write( data, offset + current_offset, builder_data.%(field)s ) ;
"""

SET_FIELD_COMPOSIT_FIXED = """
    var fieldData  = builder_data.%(field)s ;
    var writeStart = offset + %(offset)d ;

    // BUG: what if dataview is too big?
    if ( fieldData instanceof DataView ) {
        convexstruct.lib.copyIntoDataViewAtOffset( data, writeStart, fieldData ) ;
    }

    else
      self.build_%(typeName)s( data, writeStart,  length - %(offset)d, fieldData ) ;    
"""

SET_FIELD_REPETED = """
    if ( builder_data.%(field)s != undefined ) {

        var arrayData  = builder_data.%(field)s ;
        var writeStart = offset + current_offset ;
        var indexStart = writeStart + 4 ;

        data.setUint32( writeStart, arrayData.length, true ) ;

        writeStart     += 4 ;
        current_offset += 4 ;

        var indexLength = 4 * arrayData.length ;

        writeStart     += indexLength ;
        current_offset += indexLength ;

        for ( var i = 0 ; i < arrayData.length ; i++ ) {
            var fieldData = arrayData[ i ] ;

            if ( fieldData === undefined )
                return 0 ;
            
            else if ( fieldData instanceof DataView ) {
                convexstruct.lib.copyIntoDataViewAtOffset( data, writeStart, fieldData ) ;

                wrote = fieldData.byteLength ;
            }

            else
               wrote = self.build_%(typeName)s( data, writeStart, length - current_offset, fieldData ) ;    


            if ( wrote == 0 )
                return 0 ;

            writeStart     += wrote ;
            current_offset += wrote ;

            data.setUint32( indexStart + ( 4 * i ), current_offset, true ) ;
        }   
    }
"""

SET_FIELD_COMPOSIT_VAR = """
    if ( builder_data.%(field)s != undefined ) {

        var fieldData  = builder_data.%(field)s ;
        var writeStart = offset + current_offset ;

        if ( fieldData instanceof DataView ) {
            convexstruct.lib.copyIntoDataViewAtOffset( data, writeStart, fieldData ) ;

            wrote = fieldData.byteLength ;
        }

        else
           wrote = self.build_%(typeName)s( data, writeStart, length - current_offset, fieldData ) ;    

    
        if ( wrote == 0 )
            return 0 ;

        current_offset += wrote ;
    }
"""


SET_FIELD_TAGGED = """
    if ( builder_data.%(field)s != undefined ) {
        var tag = builder_data.%(field)s.tag ;

        var tag64 = new convexstruct.lib.Uint64 (
            convexstruct.lib.hexToUint32( tag, 4 ) ,
            convexstruct.lib.hexToUint32( tag, 0 ) );
            
        convexstruct.types.uint64.write( data, offset + current_offset, tag64 ) ;

        current_offset += 8 ;

        var builder = convexstruct.registry.builder( tag ) ;


        var fieldData  = builder_data.%(field)s.data ;
        var writeStart = offset + current_offset ;

        if ( fieldData instanceof DataView ) {
            convexstruct.lib.copyIntoDataViewAtOffset( data, writeStart, fieldData ) ;

            wrote = fieldData.byteLength ;
        }

        else
           wrote = builder( data, writeStart, length - current_offset, fieldData ) ;    

        if ( wrote == 0 )
            return 0 ;

        current_offset += wrote ;
    }
"""



COMPUTE_LENGTH_START = """
self.compute_%(message)s_length = function ( builder ) {\n
    if ( builder instanceof DataView )
        return builder.byteLength ;
"""

SET_END = "    data.setUint32( offset + %(index)d * 4, current_offset, true ) ;"


COMPUTE_FIXED_LENGTH = """
self.compute_%(message)s_length = function ( builder ) {
    return %(width)d ;
} ;
"""

COMPUTE_TAGGED_LENGTH = """
    if ( builder.%(name)s != undefined ) {
        length += 8 ;
        var computer = convexstruct.registry.computer( builder.%(name)s.tag ) ;

        length += computer( builder.%(name)s.data ) ;
    }
"""

COMPUTE_REPETED_LENGTH = """
    if ( builder.%(name)s != undefined ) {
        length += 4 ; // field count
        length += builder.%(name)s.length * 4 ;

        for ( var r = 0 ; r < builder.%(name)s.length ; r++ )
            length += self.compute_%(typeName)s_length( builder.%(name)s[r] ) ;
    }
"""

GET_FIXED_LENGTH = """
self.%(message)s_length = function ( data, offset ) {
    return %(width)d ;
} ;
"""

GET_VAR_LENGTH = """
self.%(message)s_length = function ( data, offset ) {
    return data.getUint32( offset, true ) ;
} ;
"""

REGISTER_COMPOSIT = """
self.%(name)s_tag = '%(tag)s' ;
convexstruct.registry.register( '%(tag)s', self.build_%(name)s, self.compute_%(name)s_length ) ;
"""

HEADDER = """
convexstruct.messages = new function () {

var self = {} ;

"""

FOOTER = """
return self ;
} ;
"""


def error ( message ):
    print message
    sys.exit( 1 )



def updateFromField ( baseDict, field ) :
    dataType = field.getType()
    typeName = dataType.getName()

    baseDict[ "typeName" ] = typeName
    baseDict[ "field"    ] = field.getName()


def printFieldFormat ( name, currentOffset, field, varIdex, formatString ) :

    width = 0

    if field.isFixed() :
        width = field.getType().getFixedWidth()
    
    baseDict = { "message" : name, "offset" : currentOffset, "index" : varIdex, "width" : width }

    updateFromField( baseDict, field )

    print formatString % baseDict

    return currentOffset + width


def printJS ( typeDb ) :

    print HEADDER

    for name, info in typeDb.items() :

        if info.isComposit( ) :

            hasComposit = False

            print "/***** type %s *****/" % ( info.getName(), )

            varIndex      = len( info.getVar( ) ) - 1
            currentOffset = OFFSET_SIZE * len( info.getVar( ) )

            for field in info.getFixed( ) :
                if field.isComposit() == True:
                    printFieldFormat( name, currentOffset, field, varIndex, FIXED_COMPOSIT_GETTER )
                else:
                    printFieldFormat( name, currentOffset, field, varIndex, FIXED_GETTER )

                printFieldFormat( name, currentOffset, field, varIndex, FIXED_LENGTH_GETTER )
                currentOffset += field.getType().getFixedWidth()


            varFields = info.getVar( )

            if len( varFields ) > 0 :
                field = varFields[ 0 ]

                if field.isRepeated() == True:
                    printFieldFormat( name, currentOffset, field, varIndex, FIRST_REPETED_GETTER )
                    
                elif field.isComposit() == True:
                    printFieldFormat( name, currentOffset, field, varIndex, FIRST_VAR_COMPOSIT_GETTER )

                elif field.getType().isDynamic() :
                    printFieldFormat( name, currentOffset, field, varIndex, FIRST_TAGGED_GETTER )
                    
                else:
                    printFieldFormat( name, currentOffset, field, varIndex, FIRST_VAR_GETTER )

                    
                printFieldFormat( name, currentOffset, field, varIndex, FIRST_VAR_LENGTH_GETTER )
                
                varIndex -= 1

            for field in varFields[ 1 : ] :                
                
                if field.isRepeated() == True:
                    printFieldFormat( name, currentOffset, field, varIndex, REPETED_GETTER )

                elif field.isComposit() == True:
                    printFieldFormat( name, currentOffset, field, varIndex, VAR_COMPOSIT_GETTER )

                elif field.getType().isDynamic() :
                    printFieldFormat( name, currentOffset, field, varIndex, TAGGED_GETTER )

                else:
                    printFieldFormat( name, currentOffset, field, varIndex, VAR_GETTER )

                printFieldFormat( name, currentOffset, field, varIndex, VAR_LENGTH_GETTER )
                varIndex -= 1


            varIndex      = len( varFields ) - 1
            currentOffset = OFFSET_SIZE * len( varFields )

            for field in varFields :
                if field.isComposit() == True or field.getType( ).isDynamic( ):
                    hasComposit = True
                    
            print SETTER_START % { "message" : name }

            if ( hasComposit == True ) :
                print "    var wrote ;"

            print "    var current_offset = %d ;" % ( info.getFixedWidth( ), )
            

            print FIXED_LENGTH_CHECK % ( info.getFixedWidth( ), )
    
            for field in info.getFixed( ) :
                if field.isComposit( ):
                    printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_COMPOSIT_FIXED )

                else :
                    printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_FIXED )

                currentOffset += field.getType().getFixedWidth()
                

            if len( varFields ) > 0:

                for field in varFields :

                    if field.isRepeated( ):
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_REPETED )

                    elif field.isComposit( ):
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_COMPOSIT_VAR )

                    elif field.getType( ).isDynamic( ) :
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_TAGGED )
                        
                    else :
                        printFieldFormat( name, currentOffset, field, varIndex, VAR_LENGTH_CHECK )
                        printFieldFormat( name, currentOffset, field, varIndex, SET_FIELD_VAR )

                    
                    printFieldFormat( name, currentOffset, field, varIndex, SET_END )
                    varIndex -= 1

            
            print "\n    return current_offset;\n} ;\n"

            if info.isFixed() :
                print GET_FIXED_LENGTH     % { "message" : name, "width" : info.getFixedWidth( ) }
                print COMPUTE_FIXED_LENGTH % { "message" : name, "width" : info.getFixedWidth( ) }

            else :
                print GET_VAR_LENGTH % { "message" : name, "width" : info.getFixedWidth( ) }

                print COMPUTE_LENGTH_START % { "message" : name }

                print "    var length = %d ;" % ( info.getFixedWidth( ), )

                for field in varFields :

                    if field.isRepeated( ):
                        print COMPUTE_REPETED_LENGTH % \
                              { "name" : field.getName( ), "typeName" : field.getType( ).getName( ) }
                    elif field.isComposit( ):
                        print "    if ( builder.%s != undefined ) length += self.compute_%s_length( builder.%s ) ;" % \
                              ( field.getName( ), field.getType( ).getName( ), field.getName( ) )

                    elif field.getType().isDynamic( ) :
                        print COMPUTE_TAGGED_LENGTH % \
                              { "name" : field.getName( ) }
                        
                    else :
                        print "    length += builder.%s.length ; " % ( field.getName(), )

                print "    return length;\n} ;"

            print  REGISTER_COMPOSIT % { "name" : name, "tag" : info.getTag( ) }
        
    print FOOTER
