#!/usr/bin/env python

# external imports
import sys
import json
import binascii
import hashlib
import os
import argparse

# internal imports
from printc  import printC
from printc2 import printC2
from printjs import printJS


VERSION_KEY = "version"
TAG_KEY     = "tag"
TYPE_KEY    = "type"
FIELDS_KEY  = "fields"

TYPE_ONE = 1
TYPE_TWO = 2

OFFSET_SIZE = 4

typeDb = {}


class DataType ( object ) :

    def __init__ ( self, name ) :
        raise NotImplementedError ( )


    def isComposite ( self ) :
        return False


    def isDynamic ( self ) :
        return False
    

    def isRepeated ( self ) :
        return False


    def getName ( self ) :
        raise NotImplementedError ( )


    def getFixed ( self ) :
        raise NotImplementedError ( )


    def getVar ( self ) :
        raise NotImplementedError ( )


    def setVersion ( self, version ) :
        raise NotImplementedError ( )


    def setTag ( self, tag ) :
        raise NotImplementedError ( )


    def addField ( fieldObject ) :
        raise NotImplementedError ( )


    def isFixed ( self ) :
        raise NotImplementedError ( )


    def getFixedWidth ( self ) :
        raise NotImplementedError ( )


    def compute ( self ) :
        raise NotImplementedError ( )



class TaggedFieldDataType ( DataType ) :

    def __init__ ( self, name ) :
        self._name = name

    def getName ( self ) :
        return self._name


    def isFixed ( self ) :
        return False


    def isDynamic ( self ) :
        return True

    
    def compute ( self ) :
        pass



class SimpleVarDataType ( DataType ) :

    def __init__ ( self, name ) :
        self._name = name


    def getName ( self ) :
        return self._name


    def isFixed ( self ) :
        return False

    def compute ( self ) :
        pass



class SimpeFixedDataType ( DataType ) :

    def __init__ ( self, name, width ) :
        self._name  = name
        self._width = width


    def getName ( self ) :
        return self._name
    

    def isFixed ( self ) :
        return True


    def getFixedWidth ( self ) :
        return self._width


    def compute ( self ) :
        pass



class CompositeDataType ( DataType ) :

    def __init__ ( self, name ) :
        self._name          = name
        self._fields        = []
        self._fixed         = True
        self._version       = None
        self._tag           = None
        self._noRecurse     = False
        self._fixedWidth    = 0

        self._computed       = False
        self._fixedFields    = []
        self._varFields      = []


    def getName ( self ) :
        return self._name


    def isComposite ( self ) :
        return True


    def getFixed ( self ) :
        return self._fixedFields


    def getVar ( self ) :
        return self._varFields


    def getFields ( self ) :
        return self._fields


    def setVersion ( self, version ) :
        if version == TYPE_ONE:
            self._fixed = False


    def setTag ( self, tag ) :
        self._tag = tag


    def getTag ( self ) :
        return self._tag


    def addField ( self, fieldObject ) :
        self._computed = False
        self._fields.append( fieldObject )


    def isFixed ( self ) :
        if self._noRecurse == True:
            return False
        
        return len( self._varFields ) == 0


    def getFixedWidth ( self ) :
        return self._fixedWidth


    def compute ( self ) :

        if self._computed == True:
            return

        if self._noRecurse == True:
            return

        self._fixedFields    = []
        self._varFields      = []

        self._noRecurse = True

        for field in self._fields :
            field.getType().compute( )

            if field.isFixed( ) == True :
                self._fixedFields.append( field )
                self._fixedWidth += field.getFixedWidth( )

            else :
                self._fixedWidth += OFFSET_SIZE
                self._varFields.append( field )
                
        self._noRecurse = False
        
        self._computed = True



class DataField ( object ) :

    def __init__ ( self, fieldName, typeName, repeated ) :
        self._fieldName = fieldName
        self._repeated  = repeated

        self._type = None

        if typeName in typeDb :
            self._type = typeDb[ typeName ]

        else :
            self._type = CompositeDataType ( typeName )
            typeDb[ typeName ] = self._type


    def getName ( self ) :
        return self._fieldName


    def getType ( self ) :
        return self._type
    

    def isRepeated ( self ) :
        return self._repeated


    def isFixed ( self ) :
        if self._repeated :
            return False
        else :
            return self._type.isFixed( )


    def getFixedWidth ( self ) :
        return self._type.getFixedWidth( )


    def isComposite ( self ) :
        return self._type.isComposite( )

def buildField ( messageField ) :
    
    # { "name" : "field1", "type" : "uint32",  "repeated" : true }

    fieldName  = None
    typeName   = None
    isRepeated  = False
    
    for key, value in messageField.items( ) :

        if key == "name" :
            fieldName = value

        elif key == "type" :
            typeName = value

        elif key == "repeated" :
            if not isinstance( value, bool ) :
                error( "repeated expected bool got %r: %r" % ( type( value ), value ) )

            isRepeated = value

        else :
            error( "unexpected field key %r in %r" % ( key , messageField ) )


    return DataField ( fieldName, typeName, isRepeated )



def buildType ( messageType ) :

    typeName = None
    version  = TYPE_TWO
    dataTag  = None
    fields   = None

    for key, value in messageType.items( ) :

        if key == VERSION_KEY :
            version = value

        elif key == TAG_KEY :
            dataTag = value

        elif key == TYPE_KEY :
            typeName = value

        elif key == FIELDS_KEY :
            fields   = value

        else :
            error( "Unexpected key %r" % key )

    if typeName is None:
        error( "Type has no name %r" % messageType )

    if dataTag is  None :
        nameHash = sha.new( typeName ).digest() ; 
        dataTag  = binascii.b2a_hex( nameHash[0:8] )
        
    elif len( dataTag ) != 16 :
        error( "tag %r should be 16 char long hex string not %r" % ( typeName, dataTag ) )
        

    typeObject = None

    if typeName in typeDb:
        typeObject = typeDb[ typeName ]

    else:
        typeObject = CompositeDataType ( typeName )

        typeDb[ typeName ] = typeObject


    typeObject.setVersion( version )
    typeObject.setTag( dataTag )


    for field in fields :

        if ( isinstance( field, unicode) ) :
             continue

        elif not isinstance( field, dict ) :
            error( "Fields of type %r but be map %r" % ( type( field ), field ) )
        
        fieldObject = buildField( field )
        typeObject.addField( fieldObject )



def error ( message ):
    sys.stderr.write( message + "\n" )
    sys.exit( 1 )

def buildDataTypes ( file_path_list ) :

    for file_path in file_path_list:
        fd = open( file_path )

        messages = json.load( fd )

        if not isinstance( messages, list ):
            error( "root of schema must be list" )

        for message in messages:
            # str is comment
            if isinstance( message, unicode ):
                continue

            if not isinstance( message, dict ):
                error( "expected a dict but got: %r" % message )

            buildType( message )
        


def initBuiltInTypes ( ):

    simpleFixed = [
        ( "uint8"   , 1  ) ,
        ( "int8"    , 1  ) ,
        ( "uint16"  , 2  ) ,
        ( "int16"   , 2  ) ,
        ( "uint32"  , 4  ) ,
        ( "int32"   , 4  ) ,
        ( "uint64"  , 8  ) ,
        ( "sha256"  , 32 ) ,
        ( "bit192"  , 24 ) ,
        ( "bit256"  , 32 ) ,
        ( "bit512"  , 64 ) ,
        ( "int64"   , 8  ) ,
        ( "float32" , 4  ) ,
        ( "float64" , 8  ) ,
        ]

    simpleVar = [ "bytes", "utf8" ]

    for name, width in simpleFixed:
        typeDb[ name ] = SimpeFixedDataType ( name, width )

    for name in simpleVar :
        typeDb[ name ] = SimpleVarDataType ( name )

    taggedName = "TaggedField"
    
    typeDb[ taggedName ] = TaggedFieldDataType ( taggedName )


def debugPrint ( typeDb ) :

    for name, info in typeDb.items() :

        print "found type %s" % ( info.getName(), )

        if info.isFixed( ) == True :
            print "  is fixed width width %d" % ( info.getFixedWidth(), )

        if info.isComposite( ) :
            print "  is composite, has %d fixed, %d var" % \
                  ( len( info.getFixed() ), len( info.getVar() ) )

            for field in info.getFields( ) :
                print "    field %s\tof type %s\tis repeated %s" % \
                      ( field.getName(), field.getType().getName(), field.isRepeated() )


USAGE = """
%s {c,js} message-type1.json [ message-type2.json ... ]
"""

def main ( args ) :

    if len( args ) < 3 :
        error( USAGE % ( args[ 0 ], ) )

    initBuiltInTypes( )
    output = args[ 1 ]
    paths  = args[ 2: ]

    buildDataTypes( paths )

    for typeObj in typeDb.values( ) :
        typeObj.compute( )

    if output == 'c1' :
        printC( typeDb )

    elif output == 'c' :
        cwd = os.path.dirname( args[ 0 ] )
        template = os.path.join( cwd, 'halite-c.mustache' )
        printC2( typeDb, template )
        
    elif output == 'js':
        printJS( typeDb )

    elif output == 'debug':
        debugPrint( typeDb )


    else:
        error( "unknown ouput type %r" % ( ouput, ) )

if __name__ == '__main__':
    main( sys.argv )
