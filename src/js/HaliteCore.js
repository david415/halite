
function HaliteCore ( fNacl, fAuthKeyPair ) {

  var REQUEST_KEY_BUILDER ;
  var REQUEST_KEY_RESPONSE_BUILDER ;
  var REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER ;
  var START_SESSION_BUILDER ;
  var START_SESSION_BOXED_DATA_BUILDER ;
  var START_SESSION_KEY_VOUCH_BUILDER ;


  var self = {} ;

  var messages = convexstruct.messages ;

  var fEphermalKeyPair ;
  var fEphermalKeyPairIndex ;
  var fOldEphermalKeyPair ;
  var fOldEphermalKeyPairIndex ;
  var fSessions ;
  var fInisheating ;

  self.rotateEphermalKey         = rotateEphermalKey ;
  self.forgetOldEphermalKey      = forgetOldEphermalKey ;
  self.makeRequestKey            = makeRequestKey ;
  self.processRequestKey         = processRequestKey ;
  self.processRequestKeyResponce = processRequestKeyResponce ;
  self.makeStartSession          = makeStartSession ;

  init( ) ;

  return self ;

  function init ( ) {

    rotateEphermalKey( ) ;
    
    fSessions = { } ;
    fInisheating = { } ;

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


  function rotateEphermalKey ( ) {
    fOldEphermalKeyPair      = fEphermalKeyPair ;
    fOldEphermalKeyPairIndex = fEphermalKeyPairIndex ;
    fEphermalKeyPair         = fNacl.crypto_box_keypair( ) ;
    fEphermalKeyPairIndex    = fNacl.to_hex( fEphermalKeyPair.boxPk ) ;
  }


  function forgetOldEphermalKey ( ) {
    fOldEphermalKeyPair = undefined ;
  }


  function makeRequestKey ( nonce, serverLongtermKey ) {

    var sesssionKeyPair = fNacl.crypto_box_keypair( ) ;

    var boxKey = fNacl.crypto_box_precompute( serverLongtermKey, sesssionKeyPair.boxSk ) ;

    var sessionIndex = fNacl.to_hex( sesssionKeyPair.boxPk ) ;

    fInisheating[ sessionIndex ] = { 
      startTime      : new Date ( ) ,
      serverLongterm : serverLongtermKey , 
      serverEphermal : undefined ,
      sessionBoxKey  : boxKey ,
    } ;

    var toBox = new Uint8Array ( 0 ) ;
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;
   
    REQUEST_SESSION_BUILDER.clientEKey = fEphermalKeyPair.boxPk ;
    REQUEST_SESSION_BUILDER.nonce      = nonce ;
    REQUEST_SESSION_BUILDER.cryptoBox  = boxed ;

    var message = messages.make_RequestKey( REQUEST_SESSION_BUILDER ) ;

    return message ;
  }


  function processRequestKey ( nonce, requestKeyMessage ) {

    var clientEphermalPKey = messages.RequestKey_read_clientEKey( requestKeyMessage, 0 ) ;
    var requestNonce       = messages.RequestKey_read_nonce( requestKeyMessage, 0 ) ;
    var cryptoBox          = messages.RequestKey_read_cryptoBox( requestKeyMessage, 0 ) ;

    var boxKey = fNacl.crypto_box_precompute( clientEphermalPKey, fAuthKeyPair.boxSk ) ;

    // BUG: I think this thorows a execption if open fails but it should be checked?
    var unBoxed = fNacl.crypto_box_open_precomputed( cryptoBox, requestNonce, boxKey ) ;

    REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER.serverEKey = fEphermalKeyPair.boxPk ;

    var toBox = messages.make_RequestKeyResponseBoxedData( REQUEST_KEY_RESPONSE_BOXED_DATA_BUILDER ) ;
    var boxed = fNacl.crypto_box_precomputed( toBox, nonce, boxKey ) ;

    REQUEST_KEY_RESPONSE_BUILDER.clientEKey = clientEphermalPKey ;
    REQUEST_KEY_RESPONSE_BUILDER.nonce      = nonce ;
    REQUEST_KEY_RESPONSE_BUILDER.cryptoBox  = boxed ;

    var messages = messages.make_RequestKeyResponse( REQUEST_KEY_RESPONSE_BUILDER ) ;

    return messages ;
  }


  function processRequestKeyResponce ( nonce, requestKeyMessageResponce ) {
    var clientEphermalPKey = messages.RequestKeyResponse_read_clientEKey( requestKeyMessageResponce, 0 ) ;
    var requestNonce       = messages.RequestKeyResponse_read_nonce( requestKeyMessageResponce, 0 ) ;
    var cryptoBox          = messages.RequestKeyResponse_read_cryptoBox( requestKeyMessageResponce, 0 ) ;

    var sessionIndex = fNacl.to_hex( clientEphermalPKey ) ;

    var sessionInfo = fInisheating[ sessionIndex ] ;

    if ( sessionInfo === undefined )
      return undefined ;

    var serverLongtermkey = sessionInfo.serverLongterm ;
    var boxKey            = sessionInfo.sessionBoxKey ;
   
    var unBoxed = fNacl.crypto_box_open_precomputed( cryptoBox, requestNonce, boxKey ) ;

    // Note: delete after box open to stop DOS attack.
    delete fInisheating[ sessionIndex ] ;

    var serverEphermalKey = messages.RequestKeyResponseBoxedData_read_serverEKey( unBoxed, 0 ) ;

    return serverEphermalKey ;
  }


  function makeStartSession ( nonce, serverLongtermKey, serverEphermalKey, connectionId, data ) {

    var sesssionKeyPair = fNacl.crypto_box_keypair( ) ;
    var boxKey          = fNacl.crypto_box_precompute( serverEphermalKey, sesssionKeyPair.boxSk ) ;

    var sessionIndex = fNacl.to_hex( sesssionKeyPair.boxPk ) ;

    fSessions[ sessionIndex ] = { 
      startTime      : new Date ( ) ,
      acked          : undefined
      serverLongterm : serverLongtermKey , 
      serverEphermal : undefined ,
      sessionBoxKey  : boxKey ,
      connectionId   : connectionId ,
    } ;

    START_SESSION_KEY_VOUCH_BUILDER.clientEKey   = sessionBoxKey.boxPk ;
    START_SESSION_KEY_VOUCH_BUILDER.connectionId = connectionId ;

    var keyVouch   = messages.make_StartSessionKeyVouch( START_SESSION_KEY_VOUCH_BUILDER ) ;
    var vouchNonce = fNacl.crypto_box_random_nonce( ) ; 

    var boxedVouch = fNacl.crypto_box( keyVouch, vouchNonce, serverEphermalKey, fAuthKeyPair.boxSk ) ;

    START_SESSION_BOXED_DATA_BUILDER.data       = data ;
    START_SESSION_BOXED_DATA_BUILDER.clientLKey = fAuthKeyPair.boxPk ;
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
      serverLongterm : serverLongtermKey , 
      serverEphermal : undefined ,
      sessionBoxKey  : boxKey ,
      connectionId   : connectionId ,
    } ;

  }

} ;
