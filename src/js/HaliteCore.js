
function HaliteCore ( fNacl ) {
  "use strict" ;

  var REQUEST_KEY_BYTE = 1 ;
  var REQUEST_KEY_BUILDER = {
    clientEKey : undefined ,
    nonce      : undefined ,
    cryptoBox  : undefined ,
  } ;


  var REQUEST_KEY_RESPONSE_BYTE = 2 ;
  var REQUEST_KEY_RESPONSE_BUILDER = {
    clientEKey : undefined ,
    nonce      : undefined ,
    cryptoBox  : undefined ,
  } ;

  var REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER = {
    serverEKey : undefined ,
  } ;

  var START_SESSION_BYTE = 3 ;
  var START_SESSION_BUILDER = {
    clientEKey : undefined ,
    serverEKey : undefined ,
    nonce      : undefined ,
    cryptoBox  : undefined ,      
  };

  var START_SESSION_BOXED_DATA_BUILDER = {
    data       : undefined ,
    clientLKey : undefined ,
    nonce      : undefined ,
    cryptoBox  : undefined ,      
  };

  var START_SESSION_KEY_VOUCH_BUILDER = {
    clientEKey   : undefined ,
    connectionId : undefined ,
  };


  var SESSION_MESSAGE_BYTE = 4 ;
  var SESSION_MESSAGE_BUILDER = {
    senderEKey : undefined , 
    cryptoBox  : undefined ,
  } ;
  
  var SESSION_MESSAGE_BOXED_DATA_BUILDER = {
    flags     : undefined ,
    userBytes : undefined ,
  } ;


  var SUCESS                 = 0 ;
  var ERROR_UNKNOWN_CHANNEL  = 1 ;
  var ERROR_DISCONNECTED     = 2 ;
  var ERROR_NOT_DISCONNECTED = 3 ;
  var ERROR_INTERNAL         = 4 ;
  var ERROR_MAX_CHANNELS     = 5 ;
  var ERROR_MESSAGE_TYPE     = 6 ;


  var STATE_CLOSED       = 1 ;
  var STATE_DISCONNECTED = 2 ;
  var STATE_HALF_SESSION = 3 ;
  var STATE_CONNECTED    = 4 ;

  var EMPTY_FLAGS         = 0 ;
  var CLOSE_SESSION_FLAGS = 1 ;
  var CLOSE_CHANNEL_FLAGS = 2 ;


  var self = {} ;

  self.SUCESS                 = SUCESS ;
  self.ERROR_UNKNOWN_CHANNEL  = ERROR_UNKNOWN_CHANNEL ;
  self.ERROR_DISCONNECTED     = ERROR_DISCONNECTED ;
  self.ERROR_NOT_DISCONNECTED = ERROR_NOT_DISCONNECTED ;
  self.ERROR_INTERNAL         = ERROR_INTERNAL ;
  self.ERROR_MAX_CHANNELS     = ERROR_MAX_CHANNELS ;

  self.STATE_CLOSED       = STATE_CLOSED ;
  self.STATE_DISCONNECTED = STATE_DISCONNECTED ;
  self.STATE_HALF_SESSION = STATE_HALF_SESSION ;
  self.STATE_CONNECTED    = STATE_CONNECTED ;


  self.ResultStruct         = ResultStruct ;
  self.ChannelIdentiyStruct = ChannelIdentiyStruct ;

  self.haliteInit    = haliteInit ;

  self.createChannel      = createChannel ;
  self.destroyChannel     = destroyChannel ;
  self.getChannelIdentity = getChannelIdentity ;

  self.openSession = openSession ;

  return self ;

  function ResultStruct ( ) {
    return {
      channelId       : undefined ,
      channelState    : undefined ,
      responseMessage : undefined ,
      userData        : undefined ,
      } ;
  }


  function ChannelIdentiyStruct ( ) {
    return {
      remotePublic  : undefined ,
      senderPublic  : undefined ,
      senderPrivate : undefined ,
    } ;
  } 

  
  function clearResultStruct ( resultStruct ) {
    resultStruct.channelId       = undefined ;
    resultStruct.channelState    = STATE_CLOSED ;
    resultStruct.responseMessage = undefined ;
    resultStruct.userData        = undefined ;
  }


  function uint8ArrayToString ( arr ) {
    return String.fromCharCode.apply( null, arr );
  }


  function possiblyRotateKey ( manager, currentTime ) {

    if ( ( currentTime - manager.ephermalKeyCreated ) >= manager.rotationAge )
      rotateEphermalKey( manager, currentTime ) ;

    if ( ( currentTime - manager.oldEphermalKeyCreated ) >= manager.maxKeyLife )
      forgetOld( manager ) ;
  }


  function forgetOld ( manager ) {
    manager.oldEphermalKeyCreated     = undefined ;
    manager.oldEphermalKeyOutstanding = undefined ;
    manager.oldEphermalKeyPair        = undefined ;
    manager.oldEphermalKeyPairIndex   = undefined ;
  }


  function rotateEphermalKey ( manager, currentTime ) {
    manager.oldEphermalKeyCreated     = manager.ephermalKeyCreated ;
    manager.oldEphermalKeyOutstanding = manager.ephermalKeyOutstanding ;
    manager.oldEphermalKeyPair        = manager.ephermalKeyPair ;
    manager.oldEphermalKeyPairIndex   = manager.ephermalKeyPairIndex ;

    initEphermalKey( manager, currentTime ) ;
  }


  function initEphermalKey ( manager, currentTime ) {
    manager.ephermalKeyCreated     = currentTime ;
    manager.ephermalKeyOutstanding = 0 ;
    manager.ephermalKeyPair        = fNacl.crypto_box_keypair( ) ;
    manager.ephermalKeyPairIndex   = uint8ArrayToString( manager.ephermalKeyPair.boxPk ) ;
  }


  function haliteInit ( maxChannels, maxKeyLife, identidyKeyPair ) {
    var result = {
      identidyPublic  : identidyKeyPair.boxPk ,
      identidyPrivate : identidyKeyPair.boxSk ,
      maxChannels     : maxChannels ,
      maxKeyLife      : maxKeyLife ,
      rotationAge     : maxKeyLife / 2 ,
      channels        : { } ,
      channelCount    : 0 ,
    } ;

    return result ;
  }


  function haliteFree( manager ) {
    return SUCESS ;
  }


  function createChannel ( manager, channelIdentiyStruct, resultStruct ) {
    
    if ( manager.channelCount >= manager.maxChannels ) {
      clearResultStruct( resultStruct ) ;
      return ERROR_MAX_CHANNELS ;
    }

    // BUG: is 128 bits enough?
    var buf = new Uint8Array( 16 ) ; 

    window.crypto.getRandomValues( buf ) ;

    vae channelId = uint8ArrayToString( buf ) ;
    var channel = { } ;

    if ( manager.channels[ channelId ] !== undefined ) {
      clearResultStruct( resultStruct ) ;
      return ERROR_INTERNAL ;
    }

    manager.channels[ channelId ] = channel ;
    
    channel.remotePublicIdent  = channelIdentiyStruct.remotePublic ;
    channel.senderPublicIdent  = channelIdentiyStruct.senderPublic ;
    channel.senderPrivateIdent = channelIdentiyStruct.senderPrivate ;
    channel.remotePublicEphem  = undefined ;
    channel.senderEphemralPair = undefined ;
    channel.boxKey             = undefined ;
    channel.nextSenderNonce    = undefined ;
    channel.nextRemoteNonce    = undefined ;
    channel.channelState       = STATE_DISCONNECTED ;
    channel.lastSentTime       = undefined ;
    channel.lastRecievedTime   = undefined ;
    channel.openBytes          = undefined ;
      
    resultStruct.channelId       = channelId ;
    resultStruct.channelState    = STATE_DISCONNECTED ;
    resultStruct.responseMessage = undefined ;
    resultStruct.userData        = undefined ;

    return SUCESS ;
  }


  function destroyChannel ( manager, channelId, resultStruct ) {

    clearResultStruct( resultStruct ) ;

    var channels = manager.channels ;
    var channel  = channels[ channelId ] ;

    if ( channel === undefined )
      return ERROR_UNKNOWN_CHANNEL ;

    delete channels[ channelId ] ;

    resultStruct.channelId    = channelId ;
    resultStruct.channelState = STATE_CLOSED ;

    if ( channel.channelState === STATE_CONNECTED )
      resultStruct.responseMessage = SessionMessage( channel, CLOSE_CHANNEL_FLAGS, "" ) ;

    return SUCESS ;
  }
   
 
  function getChannelIdentity ( manager, channelId, channelIdentiyStruct ) {

    var channel  = manager.channels[ channelId ] ;

    var result ;

    if ( channel === undefined ) {
      result = ERROR_UNKNOWN_CHANNEL ;
      channelIdentiyStruct.remotePublic  = undefined ;
      channelIdentiyStruct.senderPublic  = undefined ;
      channelIdentiyStruct.senderPrivate = undefined ;
    }

    else {
      result = SUCESS ;
      channelIdentiyStruct.remotePublic  = channel.remotePublicIdent ;
      channelIdentiyStruct.senderPublic  = channel.senderPublicIdent ;
      channelIdentiyStruct.senderPrivate = channel.senderPrivateIdent ;
    }

    return result ;
  }


  function openSession ( manager, channelId, currentTime, resultStruct, userBytes ) {

    clearResultStruct( resultStruct ) ;

    var channel  = manager.channels[ channelId ] ;

    if ( channel === undefined )
      return ERROR_UNKNOWN_CHANNEL ;

    if ( channel.channelState !== STATE_CLOSED ) {
      resultStruct.channelId = channelchannelId ;
      return ERROR_NOT_DISCONNECTED ;
    }

    var sesssionKeyPair = fNacl.crypto_box_keypair( ) ;

    var boxKey = fNacl.crypto_box_precompute( channel.remotePublicIdent, sesssionKeyPair.boxSk ) ;

    var toBox = new Uint8Array ( 32 ) ; // Padding
    var nonce = nacl.crypto_box_random_nonce() ;
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;
   
    REQUEST_KEY_BUILDER.clientEKey = sesssionKeyPair.boxPk ;
    REQUEST_KEY_BUILDER.nonce      = nonce ;
    REQUEST_KEY_BUILDER.cryptoBox  = boxed ;

    var messageLength = compute_RequestKey_length( REQUEST_KEY_BUILDER ) ;
    var messageBuffer = new ArrayBuffer ( messageLength + 1 ) ;
    var messageView   = new DataView ( messageBuffer ) ;

    messageView.setUint8( 0, REQUEST_KEY_BYTE ) ;

    var wrote = self.build_RequestKey( messageView, 1, messageLength, REQUEST_KEY_BUILDER ) ;

    if ( wrote !== messageLength )
      return ERROR_INTERNAL ;

    resultStruct.channelId       = channel.channelId ;
    resultStruct.channelState    = STATE_HALF_SESSION ;
    resultStruct.responseMessage = new Uint8Array ( messageBuffer ) ;

    incrmentUint8Array( nonce ) ;
    var remoteNonce = new Uint8Array ( nonce ) ;
    incrmentUint8Array( remoteNonce ) ;

    channel.senderEphemralPair = sesssionKeyPair ;
    channel.boxKey             = boxKey ;
    channel.nextSenderNonce    = nonce ;
    channel.nextRemoteNonce    = remoteNonce ;
    channel.channelState       = STATE_HALF_SESSION ;
    channel.lastSentTime       = currentTime ;
    channel.openBytes          = userBytes ;    
    
    return SUCESS ;
  }


  function closeSession ( manager, channelId, currentTime, resultStruct, userBytes ) {

    clearResultStruct( resultStruct ) ;

    var channel  = manager.channels[ channelId ] ;

    if ( channel === undefined )
      return ERROR_UNKNOWN_CHANNEL ;

    if ( channel.channelState !== STATE_CONNECTED ) {
      resultStruct.channelId = channelchannelId ;
      return ERROR_DISCONNECTED ;
    }

    var message = SessionMessage( channel, CLOSE_SESSION_FLAGS, userBytes ) ;

    channel.senderEphemralPair = undefined ;
    channel.boxKey             = undefined ;
    channel.nextSenderNonce    = undefined ;
    channel.nextRemoteNonce    = undefined ;
    channel.channelState       = STATE_DISCONNECTED ;
    channel.lastSentTime       = currentTime ;
    channel.openBytes          = undefined ;    

    resultStruct.channelId       = channel.channelId ;
    resultStruct.channelState    = channel.channelState ;
    resultStruct.responseMessage = message ;

    return SUCESS ;
  }


  function sendData ( manager, channelId, currentTime, resultStruct, userBytes ) {
    clearResultStruct( resultStruct ) ;

    var channel  = manager.channels[ channelId ] ;

    if ( channel === undefined )
      return ERROR_UNKNOWN_CHANNEL ;

    if ( channel.channelState !== STATE_CONNECTED ) {
      resultStruct.channelId = channelchannelId ;
      return ERROR_DISCONNECTED ;
    }

    var message = SessionMessage( channel, EMPTY_FLAGS, userBytes ) ;

    channel.lastSentTime = currentTime ;

    resultStruct.channelId       = channel.channelId ;
    resultStruct.channelState    = channel.channelState ;
    resultStruct.responseMessage = message ;

    return SUCESS ;
  }


  function receiveEnvlope ( manager, currentTime, resultStruct, envlopeBytes ) {
    var result ;

    clearResultStruct( resultStruct ) ;

    var typeByte = envlopeBytes[ 0 ] ;

    var envlopeView = new DataView (
      envlopeBytes.buffer, 
      envlopeBytes.byteOffset + 1, 
      envlopeBytes.byteLength - 1 
      ) ;

    if ( typeByte === REQUEST_KEY_BYTE ) 
      result = processRequestKey( manager, envlopeView, currentTime, resultStruct ) ;

    else if ( typeByte === REQUEST_KEY_RESPONSE_BYTE ) 
      processRequestKeyResponce( manager, envlopeView, currentTime, resultStruct ) ;

    else if ( typeByte === START_SESSION_BYTE  ) ;

    else if ( typeByte === SESSION_MESSAGE_BYTE  ) ;

    else {
      result = ERROR_MESSAGE_TYPE ;
    }

    return result ;
  }


  /*
    tickChannel ( manager, channelId, currentTime, resultStruct ) -> errorCode
    tickManager ( manager, currentTime ) -> errorCode ;
  */

  ////////// messages processors //////////

  function processRequestKey ( manager, requestKeyMessage, currentTime, resultStruct ) {

    possiblyRotateKey( manager, currentTime ) ;

    var clientEphermalPKey = messages.RequestKey_read_clientEKey( requestKeyMessage, 0 ) ;
    var requestNonce       = messages.RequestKey_read_nonce( requestKeyMessage, 0 ) ;
    var cryptoBox          = messages.RequestKey_read_cryptoBox( requestKeyMessage, 0 ) ;

    var boxKey = fNacl.crypto_box_precompute( clientEphermalPKey, manager.identidyPrivate ) ;

    // BUG: I think this thorows a execption if open fails but it should be checked?
    var unBoxed = fNacl.crypto_box_open_precomputed( cryptoBox, requestNonce, boxKey ) ;

    manager.ephermalKeyOutstanding++ ;

    REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER.serverEKey = manager.ephermalKeyPair.boxPk ;
    
    var toBox = messages.make_RequestKeyResponseBoxedData( REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER ) ;
    var nonce = nacl.crypto_box_random_nonce() ;
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;

    REQUEST_KEY_RESPONSE_BUILDER.clientEKey = clientEphermalPKey ;
    REQUEST_KEY_RESPONSE_BUILDER.nonce      = nonce ;
    REQUEST_KEY_RESPONSE_BUILDER.cryptoBox  = boxed ;

    var messageLength = compute_RequestKeyResponse_length( REQUEST_KEY_RESPONSE_BUILDER ) ;
    var messageBuffer = new ArrayBuffer ( messageLength + 1 ) ;
    var messageView   = new DataView ( messageBuffer ) ;

    messageView.setUint8( 0, REQUEST_KEY_RESPONSE_BYTE ) ;

    var wrote = self.build_RequestKeyResponse( messageView, 1, messageLength, REQUEST_KEY_RESPONSE_BUILDER ) ;

    if ( wrote !== messageLength )
      return ERROR_INTERNAL ;

    resultStruct.channelState    = STATE_CLOSED ;
    resultStruct.responseMessage = new Uint8Array ( messageBuffer ) ;

    return SUCESS ;
  }


  function processRequestKeyResponce ( manager, requestKeyMessageResponce, currentTime, resultStruct ) {

    var clientEphermalPKey = messages.RequestKeyResponse_read_clientEKey( requestKeyMessageResponce, 0 ) ;
    var requestNonce       = messages.RequestKeyResponse_read_nonce( requestKeyMessageResponce, 0 ) ;
    var cryptoBox          = messages.RequestKeyResponse_read_cryptoBox( requestKeyMessageResponce, 0 ) ;

    // BOOG stoped working hear... code below is incorrect.

    var sessionIndex = fNacl.to_hex( clientEphermalPKey ) ;
    var channelId    = fSessions[ sessionIndex ] ;
    var channelInfo  = fChannels[ channelId ] ;

    if ( channelInfo === undefined )
      return undefined ;

    var serverIdentitykey = sessionInfo.remoteIdentityKey ;
    var boxKey            = sessionInfo.boxKey ;
   
    var unBoxed = fNacl.crypto_box_open_precomputed( cryptoBox, requestNonce, boxKey ) ;

    var serverEphermalKey = messages.RequestKeyResponseBoxedData_read_serverEKey( unBoxed, 0 ) ;
    var sessionKeyPair    = sessionInfo.keyPair ;

    sessionInfo.state     = STATE_UNAUTHENCATED ;
    sessionInfo.remoteKey = serverEphermalKey ;
    sessionInfo.boxKey    = fNacl.crypto_box_precompute( serverEphermalKey, sessionKeyPair.boxSk ) ;

    return channelId ;
  }


  function processRequestStartSession ( nonce, startSessionMessage ) {

    var clientEphermalKey = messages.StartSession_read_clientEKey( startSessionMessage, 0 ) ;
    var serverEphermalKey = messages.StartSession_read_serverEKey( startSessionMessage, 0 ) ;
    var startNonce        = messages.StartSession_read_nonce( startSessionMessage, 0 ) ;
    var cryptoBox         = messages.StartSession_read_cryptoBox( startSessionMessage, 0 ) ;

    var sessionKeyPair ;
    var serverKeyIndex = fNacl.to_hex( serverEphermalKey ) ;

    if ( serverKeyIndex === fEphermalKeyPairIndex )
      sessionKeyPair = fEphermalKeyPair ;

    else if ( serverKeyIndex === fOldEphermalKeyPairIndex )
      sessionKeyPair = fOldEphermalKeyPair ;

    else
      return undefined ;

    var sessionIndex = fNacl.to_hex( clientEphermalKey ) ;

    if ( fSessions[ sessionIndex ] !== undefined )
      return undefined ;

    var boxKey = fNacl.crypto_box_precompute( clientEphermalKey, sesssionKeyPair.boxSk ) ;

    var boxData = fNacl.crypto_box_open_precomputed( cryptoBox, startNonce, boxKey ) ;

    // bed time stopping hear...

    fSessions[ sessionIndex ] = { 
      startTime      : new Date ( ) ,
      acked          : true , // With out cookies this is kinda a lie.
      serverIdentity : serverIdentityKey , 
      serverEphermal : undefined ,
      sessionBoxKey  : boxKey ,
      connectionId   : connectionId ,
    } ;

  }

  function makeStartSession ( nonce, serverIdentityKey, serverEphermalKey, connectionId, data ) {

    var sesssionKeyPair = fNacl.crypto_box_keypair( ) ;
    var boxKey          = fNacl.crypto_box_precompute( serverEphermalKey, sesssionKeyPair.boxSk ) ;

    var sessionIndex = fNacl.to_hex( sesssionKeyPair.boxPk ) ;

    fSessions[ sessionIndex ] = { 
      startTime      : new Date ( ) ,
      acked          : undefined
      serverIdentity : serverIdentityKey , 
      serverEphermal : undefined ,
      sessionBoxKey  : boxKey ,
      connectionId   : connectionId ,
    } ;

    START_SESSION_KEY_VOUCH_BUILDER.clientEKey   = sessionBoxKey.boxPk ;
    START_SESSION_KEY_VOUCH_BUILDER.connectionId = connectionId ;

    var keyVouch   = messages.make_StartSessionKeyVouch( START_SESSION_KEY_VOUCH_BUILDER ) ;
    var vouchNonce = fNacl.crypto_box_random_nonce( ) ; 

    var boxedVouch = fNacl.crypto_box( keyVouch, vouchNonce, serverEphermalKey, fIdentityKeyPair.boxSk ) ;

    START_SESSION_BOXED_DATA_BUILDER.data       = data ;
    START_SESSION_BOXED_DATA_BUILDER.clientLKey = fIdentityKeyPair.boxPk ;
    START_SESSION_BOXED_DATA_BUILDER.nonce      = vouchNonce ;
    START_SESSION_BOXED_DATA_BUILDER.cryptoBox  = boxedVouch ;      

    var toBox = messages.make_StartSessionBoxedData( START_SESSION_BOXED_DATA_BUILDER ) ;
    
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;

    START_SESSION_BUILDER.clientEKey = sessionBoxKey.boxPk ;
    START_SESSION_BUILDER.serverEKey = serverEphermalKey ;
    START_SESSION_BUILDER.nonce      = nonce ;
    START_SESSION_BUILDER.cryptoBox  = boxed ;      

    var startSessionMessage = messages.make_StartSession( START_SESSION_BUILDER ) ;

    return startSessionMessage ;
  }

  ////////// envlope builders //////////

  function SessionMessage ( channel, flags, userBytes ) {

    var boxKey    = channel.boxKey ;
    var nonce     = channel.nextSenderNonce ;
    var senderKey = channel.senderPublicIdent ;


    SESSION_MESSAGE_BOXED_DATA_BUILDER.flags     = flags ;
    SESSION_MESSAGE_BOXED_DATA_BUILDER.userBytes = userBytes ;

    var toBox = messages.make_SessionMessageBoxedData( SESSION_MESSAGE_BOXED_DATA_BUILDER ) ;

    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;

    incrmentUint8Array( channel.nextSenderNonce ) ;

    SESSION_MESSAGE_BUILDER.senderEKey = senderKey;
    SESSION_MESSAGE_BUILDER.cryptoBox  = boxed ;


    var messageLength = compute_RequestKey_length( SESSION_MESSAGE_BUILDER ) ;
    var messageBuffer = new ArrayBuffer ( messageLength + 1 ) ;
    var messageView   = new DataView ( messageBuffer ) ;

    messageView.setUint8( 0, SESSION_MESSAGE_BYTE ) ;

    var wrote = self.build_RequestKey( messageView, 1, messageLength, SESSION_MESSAGE_BUILDER ) ;

    if ( wrote !== messageLength )
      return ERROR_INTERNAL ;

    return new Uint8Array ( messageBuffer ) ;
  }


  //////// uitility ////////

  function incrmentUint8Array ( buffer ) {
    // little endian
    for ( var i = 0 ; i < buffer.lenght ; i++ ) {

      if ( buffer[ i ] === 255 )
        buffer[ i ] = 0 ;

      else {
        buffer[ i ] += 1 ;
        break ;
      }

    }
  }
    

}

