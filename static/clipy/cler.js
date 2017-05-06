cler
/**
 * Clipy Server Tools
 */
=(function(){"use strict";

  /////////////////////////////////////////////////////////////////////////////
  // Public Functions

  /**
   * Periodically check the server for active download progress
   */
  function check_progress() {
    http.get('/api/progress')
    .then( json.parse         )
    .then( clui.show_progress )
    .fail( _bail              )
  }

  /**
   * Shutdown the server
   */
  function shutdown() {
    http.get('/api/shutdown')
    .then( json.parse  )
    .then( console.log )
    .fail( _bail       )
  }

  /////////////////////////////////////////////////////////////////////////////
  // Private Functions

  function _bail( e ) {
    console.log(e)
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    check_progress: check_progress,
    shutdown: shutdown,
  }

}())
