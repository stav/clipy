json
/**
 * Clipy Tools - JSON utilities
 *
 * Inject global namespace: json
 */
=(function(){"use strict";

  /*
   * Parse the string and return a JSON object representation.
   *
   * If the string cannot be parsed into JSON then string itself is returned.
   */
  function parse( string ) {
    try {
      return JSON.parse( string || null )
    }
    catch ( error ) {
      console.log('Error in '+ string )
      console.log( error )
      return string.replace(/\n/g, '')
    }
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    parse: parse
  }

}())
