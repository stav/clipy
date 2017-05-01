http
/**
 * Clipy Tools - HTTP utilities
 *
 * Inject global namespace: http
 */
=(function(){"use strict";

  /*
   * HTTP GET
   *
   * Promise-based async text loader using Q
   *
   * https://github.com/bellbind/using-promise-q#setup-q-module
   */
  function get( url ) {
    let
      deferred = Q.defer(),
      request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) return;
      if (/^[^2]\d\d$/.exec(request.status))
        return deferred.reject(request.status)
      deferred.resolve(request.responseText)
    }
    request.open("GET", url, true)
    try {
      request.send()
    }
    catch ( error ) {
      deferred.reject( error )
    }
    return deferred.promise
  }

  /*
   * HTTP POST
   *
   * Callback-based async post
   */
  function post( url, string, callback, errback ) {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = callback;
    xhr.onerror = errback;
    xhr.send( string );
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    get: get,
    post: post,
  }

}())
