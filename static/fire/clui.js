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
   *
   * We get back JSON in the response and convert it to an object then load it into the the cache
   * and then insert a display panel for it.
   */
  function inquire() {
    let
      video = document.getElementById('input-video').value,
      url = '/api/inquire?video=' + video,
      _;

    http.get( url )
    .then( json.parse  )
    .then( _inload     )
    .then( _insert     )
    .fail( console.log )
  }

  /**
   * Display the progress bars
   *
   * data: [ { bytesdone: 91750, elapsed: 7.58, total: 627020, url: https://r2---sn..." },... ]
   */
  function show_progress( data ) {
    if ( data ) {
      console.log('show_progress')
      console.log(data)
      _add_active_progress_bars( data )
      _remove_dead_progress_bars( data )
    }
  }

  /**
   * Remove all panels
   */
  function clear() {
    let
      old_panels = document.getElementById('panels'),
      new_panels = document.createElement('ol'),
      contaniner = document.getElementById('panels-container'),
      _;

    // clipy_cache = { 0: null };
    // clipy_index = 1;

    old_panels.remove()
    new_panels.setAttribute('id', 'panels')
    contaniner.appendChild( new_panels )
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
   * Surround the given streams list with corresponding html
   */
  function _markup_streams( streams, vid ) {
    let
      list = document.createElement('ol'),
      _;

    for ( let i = 0; i < streams.length; i++ ) {
      const
        item = document.createElement('li'),
        text = document.createTextNode( streams[i] );

      item.setAttribute('class', 'stream')
      item.setAttribute('stream', i )
      item.setAttribute('vid', vid )
      item.appendChild( text )
      item.addEventListener('click', _download, false)

      list.setAttribute('start', 0 )
      list.appendChild( item )
    }
    return list
  }

  /**
   * Load the data into the cache
   */
  function _inload( data ) {
    if ( 'error' in data ) {
      console.log(data.error)
      console.log(data)
      return
    }
    // clipy_cache[ clipy_index++ ] = data;

    return data; // chaining
  }

  /**
   * Display the data summary in a new panel
   */
  function _insert( data ) {
    let
      text = document.createElement('span'),
      panel = document.createElement('li'),
      panels = document.getElementById('panels'),
      details = _get_details( data ),
      _;

    text.innerText = data.title;
    text.setAttribute('class', 'toggle')
    text.addEventListener('click', _toggle, false)

    panel.setAttribute('class', 'panel')
    panel.setAttribute('title', data.vid )
    panel.setAttribute('vid', data.vid )
    panel.appendChild( text )
    panel.appendChild( details )
    panels.appendChild( panel )

    return data; // chaining
  }

  /**
   * Construct the video data details
   */
  function _get_details( data ) {
    let
      list = document.createElement('dl'),
      details = document.createElement('div'),
      _;

    for (const [key,val] of es.objectEntries( data )) {
      let value = key === 'streams' ? _markup_streams( val, data.vid ) : _markup_value( val );
      let term = document.createElement('dt'); term.appendChild( document.createTextNode( key ))
      let item = document.createElement('dd'); item.appendChild( value )
      // console.log(`${key}: ${value}`);
      list.appendChild( term )
      list.appendChild( item )
    }
    details.style.display = 'none';
    details.setAttribute('class', 'details')
    details.appendChild( list )

    return details
  }

  /**
   * Show / hide the video details
   */
  function _toggle( e ) {
    let
      style = e.target.parentElement.children[1].style;

    if ( style.display === 'none' )
      style.display = '';
    else
      style.display = 'none';
  }

  /**
   * Get the goods
   */
  function _download( e ) {
    let
      vid = e.target.attributes.vid.value,
      stream = e.target.attributes.stream.value,
      url = '/api/download?vid=' + vid + '&stream=' + stream,
      _;

    http.get( url )
    .then( json.parse  )
    .then( console.log )
    .fail( console.log )
  }

  /**
   * Display the progress bars
   *
   * data: [ { bytesdone: 91750, elapsed: 7.58, total: 627020, url: https://r2---sn..." },... ]
   */
  function _add_active_progress_bars( data ) {
    for ( let stream of data.actives ) {
      console.log('active')
      console.log(stream)
      let
        progress = document.getElementById( stream.url ),
        item = undefined,
        _;

      if ( !progress ) {
        progress = document.createElement('progress');
        progress.id = stream.url;
        progress.setAttribute('title', stream.name )
        item = document.createElement('li');
        item.appendChild( progress )
        document.getElementById('progress-bars').appendChild( item )
      }
      progress.setAttribute('value', stream.bytesdone )
      progress.setAttribute('max', stream.total )
    }
  }

  /**
   * Remove and progress bars that are no longer active
   *
   * data: [ { bytesdone: 91750, elapsed: 7.58, total: 627020, url: https://r2---sn..." },... ]
   */
  function _remove_dead_progress_bars( data ) {
    let
      bars = document.getElementsByTagName('progress'),
      _;

    for (let i = bars.length - 1; i >= 0; i--) {
      let progress = bars.item(i);

      function active_url( value, index ) {
        return value.url === progress.id
      }

      if ( !data.actives.find( active_url ) ) {
        console.log('remove')
        console.log( progress )
        progress.parentElement.remove()
      }
    }
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    show_progress: show_progress,
    inquire: inquire,
    clear: clear,
  }

}())
