clui
/**
 * Clipy Tools - User Interface
 *
 * Inject global namespace: clui
 */
=(function(){"use strict";

  /////////////////////////////////////////////////////////////////////////////
  // Public Functions

  /**
   * Request a video inquiry for the particulars like title, duration and description
   */
  function inquire() {
    let
      video = document.getElementById('input-video').value,
      url = '/api/test?video=' + video,
      _;

    http.get( url )
    .then( json.parse  )
    .then( _insert     )
    .fail( console.log )
  }

  /**
   * Get the goods
   */
  function download() {
    console.log('NotImplemented Error')
  }

  /**
   * Remove all panels
   */
  function clear() {
    let
      // panels = document.getElementsByClassName('panel'),
      panels = document.getElementById('panels'),
      contaniner = document.getElementById('panels-container'),
      _;

    panels.remove()
    panels = document.createElement('div')
    panels.setAttribute('id', 'panels')
    contaniner.appendChild( panels )
  }

  /////////////////////////////////////////////////////////////////////////////
  // Private Functions

  /**
   * Surround the given value with corresponding html
   */
  function _markup_value( o ) {
    if ( u.isArray( o )) {
      let
        list = document.createElement('ul'),
        _;
      for ( let i = 0; i < o.length; i++ ) {
        const
          item = document.createElement('li'),
          text = document.createTextNode( o[i] );
        item.appendChild( text )
        list.appendChild( item )
      }
      return list
    }
    return document.createTextNode( o )
  }

  /**
   * Display the response in a new panel
   */
  function _insert( response ) {
    if ( 'error' in response ) {
      console.log(response.error)
      console.log(response)
      return
    }
    let
      list = document.createElement('dl'),
      panel = document.createElement('div'),
      panels = document.getElementById('panels'),
      _;

    for (const [key,value] of es.objectEntries( response )) {
      const
        term = document.createElement('dt'),
        item = document.createElement('dd');
      term.appendChild( document.createTextNode( key ))
      item.appendChild( _markup_value( value ))
      // console.log(`${key}: ${value}`);
      list.appendChild( term )
      list.appendChild( item )
    }

    panel.setAttribute('class', 'panel')
    panel.appendChild( list )
    panels.appendChild( panel )
    // document.body.insertBefore(panel, currentDiv);
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    download: download,
    inquire: inquire,
    clear: clear,
  }

}())
