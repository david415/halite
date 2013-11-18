
function HaliteCore ( fNacl, fIdentityKeyPair, fInitTime, fMaxKeyAge ) {

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
