clui
/**
 * Clipy Tools - User Interface
 *
 * Inject global namespace: clui
 */
=(function(){"use strict";

  /**
   * Display the response in a new panel
   */
  function premier( response ) {
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

    panel.setAttribute( 'class', 'panel' );
    panel.appendChild( list )
    panels.appendChild( panel )
    // document.body.insertBefore(panel, currentDiv);
  }

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
   * Remove all panels
   */
  function clear() {
    let
      panels = document.getElementsByClassName('panel'),
      _;

    for (let panel of panels) {
      panel.remove()
    }
  }


  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    premier: premier,
    clear:   clear,
  }

}())
