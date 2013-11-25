
function HaliteCore ( fNacl ) {
  "use strict" ;

  var REQUEST_KEY_BUILDER = {
    clientEKey : undefined ,
    nonce      : undefined ,
    cryptoBox  : undefined ,
  } ;

  var REQUEST_KEY_RESPONSE_BUILDER = {
    clientEKey : undefined ,
    nonce      : undefined ,
    cryptoBox  : undefined ,
  } ;

  var REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER = {
    serverEKey : undefined ,
  } ;

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

  var SUCESS                 = 0 ;
  var ERROR_UNKNOWN_CHANNEL  = 1 ;
  var ERROR_DISCONNECTED     = 2 ;
  var ERROR_NOT_DISCONNECTED = 3 ;
  var ERROR_INTERNAL         = 4 ;
  var ERROR_MAX_CHANNELS     = 5 ;

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


  function haliteInit ( maxChannels, maxKeyLife ) {
    var result = {
      maxChannels  : maxChannels ,
      maxKeyLife   : maxKeyLife ,
      rotationAge  : maxKeyLife / 2 ,
      channels     : { } ,
      channelCount : 0 ,
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

    if ( channel.channelState === STATE_CONNECTED ) {
      var messageResult = SessionMessage( channel, resultStruct, CLOSE_CHANNEL_FLAGS, "" ) ;
      
      if ( messageResult !== SUCESS )
        return ERROR_INTERNAL ;
    }

    return SUCESS ;
  }
   
 
  function getChannelIdentity ( manager, channelId, channelIdentiyStruct ) {

    var channels = manager.channels ;
    var channel  = channels[ channelId ] ;

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

    var channels = manager.channels ;
    var channel  = channels[ channelId ] ;

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
   
    REQUEST_SESSION_BUILDER.clientEKey = sesssionKeyPair.boxPk ;
    REQUEST_SESSION_BUILDER.nonce      = nonce ;
    REQUEST_SESSION_BUILDER.cryptoBox  = boxed ;

    var message = messages.make_RequestKey( REQUEST_SESSION_BUILDER ) ;

    resultStruct.channelId       = channel.channelId ;
    resultStruct.channelState    = STATE_HALF_SESSION ;
    resultStruct.responseMessage = messages ;

    channel.senderEphemralPair = sesssionKeyPair ;
    channel.boxKey             = boxKey ;
    channel.channelState       = STATE_HALF_SESSION ;
    channel.lastSentTime       = currentTime ;
    channel.openBytes          = userBytes ;    
    
    return SUCESS ;
  }


  function closeSession ( manager, channelId, currentTime, resultStruct, userBytes ) {

    clearResultStruct( resultStruct ) ;

    var channels = manager.channels ;
    var channel  = channels[ channelId ] ;

    if ( channel === undefined )
      return ERROR_UNKNOWN_CHANNEL ;

    if ( channel.channelState !== STATE_CONNECTED ) {
      resultStruct.channelId = channelchannelId ;
      return ERROR_DISCONNECTED ;
    }
    
    var message = SessionMessage( channel.boxKey, CLOSE_SESSION_FLAGS, userBytes ) ;

  }


  sendData     ( manager, channelId, currentTime, resultStruct, userBytes ) -> errorCode

  receiveEnvlope ( manager, currentTime, resultStruct, envlopeBytes ) -> errorCode

  tickChannel ( manager, channelId, currentTime, resultStruct ) -> errorCode
  tickManager ( manager, currentTime ) -> errorCode ;


  ////////// envlope builders //////////

  function SessionMessage ( channel.boxKey, flags, userBytes ) {
    
  }

}
  ///////////////////////////////////////////

function HaliteCoreOld ( fNacl, fIdentityKeyPair, fInitTime, fMaxKeyAge ) {

  var STATE_DISCONNECTED    = 0 ;
  var STATE_REQUESTING_KEY  = 1 ;
  var STATE_UNAUTHENCATED   = 2 ;
  var STATE_CONNECTED       = 4 ;
  var STATE_CLOSING_SESSION = 5 ;
  var STATE_CLOSING_CHANNEL = 6 ;
  var STATE_CLOSED          = 7 ;

  var SUCESS                 = 0 ;
  var ERROR_NO_CHANNEL       = 1 ;
  var ERROR_NOT_DISCONNECTED = 2 ;
  var ERROR_NOT_CONNECTED    = 3 ;

  var REQUEST_KEY_BUILDER ;
  var REQUEST_KEY_RESPONSE_BUILDER ;
  var REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER ;
  var START_SESSION_BUILDER ;
  var START_SESSION_BOXED_DATA_BUILDER ;
  var START_SESSION_KEY_VOUCH_BUILDER ;


  var self = {} ;

  var messages = convexstruct.messages ;

  var fEphermalKeyCreated ;
  var fEphermalKeyOutstanding ;
  var fEphermalKeyPair ;
  var fEphermalKeyPairIndex ;
  var fOldEphermalKeyCreated ;
  var fOldEphermalKeyOutstanding ;
  var fOldEphermalKeyPair ;
  var fOldEphermalKeyPairIndex ;
  var fRotationAge ;

  var fMaxChannelId ;
  var fFreeChannelIds ;

  var fSessions ;
  var fChannels ;

  self.createChannel  = createChannel ;
  self.destroyChannel = destroyChannel ;
  self.openSession    = openSession ;

  self.closeSession   = closeSession ;
  self.sendData       = sendData ;
  self.receiveData    = receiveEnvlope ;
  self.tick           = tick ;

  init( ) ;

  return self ;

  function init ( ) {

    fRotationAge = fMaxKeyAge / 2 ;

    initEphermalKey( fInitTime ) ;
    
    fSessions = { } ;
    fChannels = { } ;

    fMaxChannelId = 0 ;
    fFreeChannelIds = [ 0 ] ;

    REQUEST_KEY_BUILDER = {
      clientEKey : undefined ,
      nonce      : undefined ,
      cryptoBox  : undefined ,
    } ;

    REQUEST_KEY_RESPONSE_BUILDER = {
      clientEKey : undefined ,
      nonce      : undefined ,
      cryptoBox  : undefined ,
    } ;

    REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER = {
      serverEKey : undefined ,
    } ;

    START_SESSION_BUILDER = {
      clientEKey : undefined ,
      serverEKey : undefined ,
      nonce      : undefined ,
      cryptoBox  : undefined ,      
    };

    START_SESSION_BOXED_DATA_BUILDER = {
      data       : undefined ,
      clientLKey : undefined ,
      nonce      : undefined ,
      cryptoBox  : undefined ,      
    };

    START_SESSION_KEY_VOUCH_BUILDER = {
      clientEKey   : undefined ,
      connectionId : undefined ,
    };


  }


  function possiblyRotateKey ( now ) {
    if ( ( now - fEphermalKeyCreated ) >= fRotationAge )
      rotateEphermalKey( now ) ;
  }


  function forgetOld ( ) {
    fOldEphermalKeyCreated = undefined ;
    fOldEphermalKeyOutstanding = undefined ;
    fOldEphermalKeyPair = undefined ;
    fOldEphermalKeyPairIndex = undefined ;
  }

  function rotateEphermalKey ( now ) {
    fOldEphermalKeyCreated     = fEphermalKeyCreated ;
    fOldEphermalKeyOutstanding = fEphermalKeyOutstanding ;
    fOldEphermalKeyPair        = fEphermalKeyPair ;
    fOldEphermalKeyPairIndex   = fEphermalKeyPairIndex ;

    initEphermalKey( now ) ;
  }

  function initEphermalKey ( now ) {
    fEphermalKeyCreated      = now ;
    fEphermalKeyPair         = fNacl.crypto_box_keypair( ) ;
    fEphermalKeyPairIndex    = fNacl.to_hex( fEphermalKeyPair.boxPk ) ;
  }


  function createChannel ( remoteIdentityKey, stateChangeCallbak, consumeCallback, errorCallback ) {

    var channelId ;

    if ( fFreeChannelIds.lenght !== 0 ) 
      channelId = fFreeChannelIds.pop( ) ;

    else {
      fMaxChannelId++ ;
      channelId = fMaxChannelId ;
    }

    fChannels[ channelId ] = {
      remoteIdentityKey  : remoteIdentityKey ,
      stateChangeCallbak : stateChangeCallbak ,
      consumeCallback    : consumeCallback ,
      errorCallback      : errorCallback ,
      lastEphermalKeyId  : undefined ,
      // session info
      state        : STATE_DISCONNECTED ,
      sentTime     : undefined ,
      receivedTime : undefined ,
      keyPair      : undefined ,
      remoteKey    : undefined ,
      boxKey       : undefined ,
      lastNonce    : undefined ,
      lastSequance : undefined ,
      messageCount : undefined ,
    } ;

    return channelId ;
  }


  function destroyChannel ( channelId ) {
    // BOOG need to actually send message and wait for response
    var result ;

    if ( fChannels[ channelId ] === undefined ) 
      result = false ;

    else {
      result = true ;
      fChannels[ channelId ] = undefined ;
      fFreeChannelIds.unshift( channelId ) ;
    }

    return result ;
  }


  function openSession ( channelId, now, result ) {

    var channelInfo = fChannels[ channelId ] ;

    if ( channelInfo === undefined ) {
      result.code  = ERROR_NO_CHANNEL  ;
      result.value = undefined ;
      return ;
    }

    if ( channelInfo.state !== STATE_DISCONNECTED ) {
      result.code  = ERROR_NOT_DISCONNECTED  ;
      result.value = undefined ;
      return ;
    }

    var serverIdentityKey = channelInfo.remoteIdentityKey ;

    var sesssionKeyPair = fNacl.crypto_box_keypair( ) ;

    var boxKey = fNacl.crypto_box_precompute( serverIdentityKey, sesssionKeyPair.boxSk ) ;

    var sessionIndex = fNacl.to_hex( sesssionKeyPair.boxPk ) ;

    fSessions[ sessionIndex ] = channelId ;

    channelInfo.state        = STATE_REQUESTING_KEY ;
    channelInfo.keyPair      = sesssionKeyPair ;
    channelInfo.boxKey       = boxKey ;
    channelInfo.sentTime     = now ;
    channelInfo.receivedTime = undefined ;

    var toBox = new Uint8Array ( 32 ) ; // Padding
    var nonce = nacl.crypto_box_random_nonce() ;
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;
   
    REQUEST_SESSION_BUILDER.clientEKey = fEphermalKeyPair.boxPk ;
    REQUEST_SESSION_BUILDER.nonce      = nonce ;
    REQUEST_SESSION_BUILDER.cryptoBox  = boxed ;

    var message = messages.make_RequestKey( REQUEST_SESSION_BUILDER ) ;

    result.code  = SUCESS ;
    result.value = messages ;

    return ;
  }


  function closeSession ( connectionId, now, result ) {

    var channelInfo = fChannels[ channelId ] ;

    if ( channelInfo === undefined ) {
      result.code  = ERROR_NO_CHANNEL  ;
      result.value = undefined ;
      return ;
    }

    if ( channelInfo.state === STATE_DISCONNECTED ) {
      result.code  = ERROR_NOT_CONNECTED  ;
      result.value = undefined ;
      return ;
    }

    

  }


  function processRequestKey ( requestKeyMessage, now, result ) {

    possiblyRotateKey( now ) ;

    var clientEphermalPKey = messages.RequestKey_read_clientEKey( requestKeyMessage, 0 ) ;
    var requestNonce       = messages.RequestKey_read_nonce( requestKeyMessage, 0 ) ;
    var cryptoBox          = messages.RequestKey_read_cryptoBox( requestKeyMessage, 0 ) ;

    var boxKey = fNacl.crypto_box_precompute( clientEphermalPKey, fIdentityKeyPair.boxSk ) ;

    // BUG: I think this thorows a execption if open fails but it should be checked?
    var unBoxed = fNacl.crypto_box_open_precomputed( cryptoBox, requestNonce, boxKey ) ;

    REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER.serverEKey = fEphermalKeyPair.boxPk ;

    var toBox = messages.make_RequestKeyResponseBoxedData( REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER ) ;
    var nonce = nacl.crypto_box_random_nonce() ;
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;

    REQUEST_KEY_RESPONSE_BUILDER.clientEKey = clientEphermalPKey ;
    REQUEST_KEY_RESPONSE_BUILDER.nonce      = nonce ;
    REQUEST_KEY_RESPONSE_BUILDER.cryptoBox  = boxed ;

    var messages = messages.make_RequestKeyResponse( REQUEST_KEY_RESPONSE_BUILDER ) ;

    result.code  = SUCESS ;
    result.value = messages ;

    return ;
  }


  function processRequestKeyResponce ( requestKeyMessageResponce, now, result ) {
    var clientEphermalPKey = messages.RequestKeyResponse_read_clientEKey( requestKeyMessageResponce, 0 ) ;
    var requestNonce       = messages.RequestKeyResponse_read_nonce( requestKeyMessageResponce, 0 ) ;
    var cryptoBox          = messages.RequestKeyResponse_read_cryptoBox( requestKeyMessageResponce, 0 ) ;

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

} ;
