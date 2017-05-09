clui
/**
 * Clipy User Interface
 */
=(function(){"use strict";

  /////////////////////////////////////////////////////////////////////////////
  // Public Functions

  /**
   * Request a video inquiry for the particulars like title, duration and description
   *
   * Can be called from either the Inquire button in which case we have no element argument and
   * we use the text box; or, this function can be called from clicking the progress bar which
   * passes us the target element which has the video Id for us to use for inquiry.
   *
   * We get back JSON in the response and convert it to an object then load it into the the cache
   * and then insert a display panel for it.
   */
  function inquire( element ) {
    let
      vid = element ? element.target.vid : undefined,
      video = vid ? vid : document.getElementById('input-video').value,
      url = '/api/inquire?video=' + encodeURIComponent(video),
      _;

    http.get( url )
    .then( json.parse  )
 // .then( _inload     )
    .then( _insert     )
    .fail( console.log )
  }

  /**
   * Display the progress bars
   *
   * Called every few seconds with the servers list of streams actively downloading
   *
   * data: { actives: [ { bytesdone: 91750, elapsed: 7.58, total: 627020, sid: "1M6sk2zD6D8|17" },... ]}
   */
  function show_progress( data ) {
    let
      status = document.getElementById('running'),
      _;

    if ( u.isObject( data ) ) {
      // Server is running since we got a valid response
      status.checked = true;

      if ( data.actives ) {
        _add_active_progress_bars( data.actives )
        _remove_dead_progress_bars( data.actives )
      }
    }
    else {
      // Server is not running since we got no response
      status.checked = false;
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
        stream = streams[i],
        item = document.createElement('li'),
        text = document.createTextNode( stream.display );

      item.setAttribute('class', 'stream')
      item.setAttribute('title', 'Download this stream')
      item.setAttribute('index', i )
      item.setAttribute('vid', vid )
      item.appendChild( text )
      item.addEventListener('click', _download, false)
      item.sid = stream.sid;

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

    return data // chaining
  }

  /**
   * Display the data summary in a new panel
   */
  function _insert( data ) {
    let
      head = _get_panel_header( data ),
      panel = document.createElement('li'),
      panels = document.getElementById('panels'),
      details = _get_details( data ),
      _;

    panel.setAttribute('class', 'panel')
    panel.setAttribute('title', data.vid )
    panel.setAttribute('vid', data.vid )
    panel.appendChild( head )
    panel.appendChild( details )
    panels.appendChild( panel )

    return data // chaining
  }

  /**
   * Construct the panel header line with togglable title and close button
   */
  function _get_panel_header( data ) {
    let
      row = document.createElement('div'),
      left = document.createElement('div'),
      right = document.createElement('div'),
      close = document.createElement('button'),
      text = document.createElement('span'),
      _;

    text.innerText = data.title;
    text.setAttribute('class', 'toggle')
    text.addEventListener('click', _toggle, false)

    left.setAttribute('class', 'eleven columns')
    left.appendChild( text )

    close.setAttribute('class', 'button close')
    close.setAttribute('title', 'Close this panel')
    close.innerText = 'X';
    close.addEventListener('click', _close, false)

    right.setAttribute('class', 'one columns')
    right.appendChild( close )

    row.setAttribute('class', 'row')
    row.appendChild( left )
    row.appendChild( right )

    return row
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
  function _close( e ) {
    let
      panel = e.target.parentElement.parentElement.parentElement;

    panel.remove()
  }

  /**
   * Show / hide the video details
   */
  function _toggle( e ) {
    let
      style = e.target.parentElement.parentElement.parentElement.children[1].style;

    if ( style.display === 'none' )
      style.display = '';
    else
      style.display = 'none';
  }

  /**
   * Get the goods
   */
  function _download( element ) {
    let
      att = element.target.attributes,
      vid = att.vid.value,
      sid = element.target.sid,
      index = att.index.value,
      progress = document.getElementById( sid ),
      url = '/api/download?vid=' + encodeURIComponent(vid) + '&stream=' + index,
      _;

    console.log('_download')
    console.log(element)
    console.log(progress)
    if ( progress ) {
      console.log('CANCEL')
      _cancel( element )
    }
    else {
      console.log('DOWNLOAD')
      http.get( url )
      .then( json.parse  )
      .then( console.log )
      .fail( console.log )
    }
  }

  /**
   * Cancel a download in progress
   */
  function _cancel( element ) {
    let
      sid = element.target.sid,
      url = '/api/cancel?sid=' + encodeURIComponent(sid),
      _;

    http.get( url )
    .then( json.parse  )
    .then( console.log )
    .fail( console.log )
  }

  /**
   * Display the progress bars
   *
   * streams: [ { bytesdone: 91750, elapsed: 7.58, total: 627020, sid: "1M6sk2zD6D8|17" },... ]
   */
  function _add_active_progress_bars( streams ) {
    for ( let stream of streams ) {
      let
        progress = document.getElementById( stream.sid ),
        bars = document.getElementById('progress-bars'),
        item, label = undefined,
        _;

      if ( !progress ) {
        progress = document.createElement('progress');
        progress.vid = stream.vid;
        progress.id = stream.sid;
        label = document.createElement('label');
        label.setAttribute('for', stream.sid )
        item = document.createElement('li');
        item.setAttribute('class', 'progress')
        item.setAttribute('title', stream.name )
        item.appendChild( progress )
        item.appendChild( label )
        item.addEventListener('click', inquire, false)
        bars.appendChild( item )
      }
      progress.setAttribute('value', stream.bytesdone )
      progress.setAttribute('max', stream.total )
      label = progress.nextElementSibling;
      label.innerText = stream.rate + ' KB/s - ' + stream.eta + ' sec';
    }
  }

  /**
   * Remove and progress bars that are no longer active
   *
   * streams: [ { bytesdone: 91750, elapsed: 7.58, total: 627020, sid: "1M6sk2zD6D8|17" },... ]
   */
  function _remove_dead_progress_bars( streams ) {
    let
      bars = document.getElementsByTagName('progress'),
      _;

    for (let i = bars.length - 1; i >= 0; i--) {
      let progress = bars.item(i);

      function active( value, index ) {
        return value.sid === progress.id
      }

      if ( !streams.find( active ) ) {
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
