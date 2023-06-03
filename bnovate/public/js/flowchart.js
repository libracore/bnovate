/* Modals.js. (c) 2023, bNovate.
 *
 * Custom flowchart to show cartridge status
 * 
 ****************************************************/

frappe.provide("bnovate.flowchart");

bnovate.flowchart.attach = function (el, order_status, cartridge_status) {
   el.innerHTML = bnovate.flowchart.svg;

   // These states should be kept in sync with the Cartridge Status report (cartridge_status.py)
   const nodes = {
      'None': '#none',
      'Requested': '#requested',
      'Confirmed': '#confirmed',
      'Ready for Refill': '#ready-to-fill',
      'Refill Pending': '#pending-fill',
      'Filling': '#filling',
      'Ready to Ship': '#ready-to-ship',
      'Shipped': '#shipped',
   }

   el.querySelector(nodes[order_status || 'None'])?.classList.add('active');
   el.querySelector(nodes[cartridge_status])?.classList.add('active');

   // Highlight node corresponding to order status
   // Highlight node corresponding to cartridge status
}

bnovate.flowchart.svg = `
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   class="cartridge-flowchart"
   host="65bd71144e"
   version="1.1"
   width="594.59198"
   height="323.43301"
   viewBox="-0.5 -0.5 594.59198 323.43302"
   id="svg128"
   sodipodi:docname="flowchart.svg"
   inkscape:version="1.2.2 (732a01da63, 2022-12-09)"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <sodipodi:namedview
     id="namedview130"
     pagecolor="#ffffff"
     bordercolor="#000000"
     borderopacity="0.25"
     inkscape:showpageshadow="2"
     inkscape:pageopacity="0.0"
     inkscape:pagecheckerboard="0"
     inkscape:deskcolor="#d1d1d1"
     showgrid="false"
     inkscape:zoom="1.2944013"
     inkscape:cx="88.457887"
     inkscape:cy="105.84044"
     inkscape:window-width="2560"
     inkscape:window-height="1375"
     inkscape:window-x="2992"
     inkscape:window-y="-8"
     inkscape:window-maximized="1"
     inkscape:current-layer="g118"
     showguides="true">
    <sodipodi:guide
       position="15.25366,133.27072"
       orientation="1,0"
       id="guide870"
       inkscape:locked="false" />
    <sodipodi:guide
       position="9.4245487,266.93589"
       orientation="1,0"
       id="guide331"
       inkscape:locked="false" />
  </sodipodi:namedview>
  <defs
     id="defs2" />
  <g
     id="g118"
     transform="translate(-48.868652,-1.8183594)">
    <rect
       x="67.740738"
       y="99.111862"
       width="569.21967"
       height="105.75093"
       fill="#fff3e6"
       stroke="none"
       pointer-events="all"
       id="rect4"
       style="stroke-width:0.910572" />
    <rect
       x="67.707603"
       y="211"
       width="569.25281"
       height="105.75093"
       fill="#e0efff"
       stroke="none"
       pointer-events="all"
       id="rect6"
       style="stroke-width:0.910597" />
    <path
       d="m 208,151 h 93.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path8" />
    <path
       d="m 306.88,151 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path10" />
    <circle
       id="ready-to-fill"
       class="node"
       cx="198"
       cy="151"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       r="10" />
    <g
       transform="translate(3.5,3.5)"
       id="g17">
      <text
         x="194"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text13">Ready to Fill</text>
    </g>
    <path
       d="m 328,151 h 93.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path19" />
    <path
       d="m 426.88,151 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path21" />
    <circle
       id="pending-fill"
       class="node"
       cx="318"
       cy="151"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       r="10" />
    <g
       transform="translate(3.5,3.5)"
       id="g28">
      <text
         x="314"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text24">Pending Fill</text>
    </g>
    <path
       d="m 448,151 h 93.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path30" />
    <path
       d="m 546.88,151 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path32" />
    <circle
       cx="438"
       cy="151"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="filling"
       class="node"
       r="10" />
    <g
       transform="translate(3.5,3.5)"
       id="g40">
      <text
         x="434"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text36">Filling</text>
    </g>
    <path
       d="m 555.23522,150.99025 h 56.71934 q 9.45322,0 9.45322,10.00163 v 100.01624 q 0,10.00163 -9.45322,10.00163 h -277.575"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path42"
       style="stroke-width:0.972356" />
    <path
       d="m 329.12,271 7,-3.5 -1.75,3.5 1.75,3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path44" />
    <circle
       cx="558"
       cy="151"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="ready-to-ship"
       class="node"
       r="10" />
    <g
       transform="translate(3.5,3.5)"
       id="g52">
      <text
         x="554"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text48">Ready to Ship</text>
    </g>
    <path
       d="M 307.98316,271.01759 H 145.53441 c -6.01662,0 -9.02493,-3.33431 -9.02493,-10.00293 V 160.98534 c 0,-6.66862 3.00831,-10.00293 9.02493,-10.00293 h 38.4007"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path54"
       style="stroke-width:0.950136"
       sodipodi:nodetypes="cssssc" />
    <path
       d="m 186.88,151 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path56" />
    <circle
       cx="318"
       cy="271"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="shipped"
       class="node"
       r="10" />
    <g
       transform="translate(3.5,3.5)"
       id="g64">
      <text
         x="314"
         y="251"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text60">Shipped to Customer</text>
    </g>
    <path
       d="m 318,41 v 93.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path66" />
    <path
       d="m 318,139.88 -3.5,-7 3.5,1.75 3.5,-1.75 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path68" />
    <circle
       cx="318"
       cy="47"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="confirmed"
       class="node"
       r="10" />
    <g
       transform="translate(3.5,19.5)"
       id="g76">
      <text
         x="314"
         y="11"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text72">Confirmed</text>
    </g>
    <path
       d="m 208,47 h 93.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path78" />
    <path
       d="m 306.88,47 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path80" />
    <circle
       cx="198"
       cy="47"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="requested"
       class="node"
       r="10" />
    <g
       transform="translate(3.5,19.5)"
       id="g88">
      <text
         x="194"
         y="11"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text84">Requested</text>
    </g>
    <path
       d="m 98,47 h 83.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path90" />
    <path
       d="m 186.88,47 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path92" />
    <circle
       cx="88"
       cy="47"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="none"
       class="node"
       r="10" />
    <g
       transform="translate(3.5,19.5)"
       id="g100">
      <text
         x="84"
         y="11"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text96">None</text>
    </g>
    <rect
       x="4"
       y="91"
       width="94"
       height="30"
       fill="none"
       stroke="none"
       pointer-events="all"
       id="rect102" />
    <g
       transform="rotate(-90,85.841064,100.7748)"
       id="g108">
      <switch
         id="switch106">
        <foreignObject
           pointer-events="none"
           width="100%"
           height="100%"
           requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"
           style="overflow: visible; text-align: left;">
          <xhtml:div
             style="display: flex; align-items: unsafe center; justify-content: unsafe flex-start; width: 83px; height: 1px; padding-top: 102px; margin-left: 11px;">
            <xhtml:div
               data-drawio-colors="color: rgb(0, 0, 0); "
               style="box-sizing: border-box; font-size: 0px; text-align: left;">
              <xhtml:div
                 style="display: inline-block; font-size: 12px; font-family: Open Sans; color: rgb(0, 0, 0); line-height: 1.2; pointer-events: all; white-space: normal; overflow-wrap: normal;">
                                At bNovate
                            </xhtml:div>
            </xhtml:div>
          </xhtml:div>
        </foreignObject>
        <text
           x="11"
           y="106"
           fill="#000000"
           font-family="'Open Sans'"
           font-size="12px"
           id="text104">At bNovate</text>
      </switch>
    </g>
    <rect
       x="4"
       y="291"
       width="94"
       height="30"
       fill="none"
       stroke="none"
       pointer-events="all"
       id="rect110" />
    <g
       transform="rotate(-90,49.733102,264.52035)"
       id="g116">
      <switch
         id="switch114">
        <foreignObject
           pointer-events="none"
           width="100%"
           height="100%"
           requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"
           style="overflow: visible; text-align: left;">
          <xhtml:div
             style="display: flex; align-items: unsafe center; justify-content: unsafe flex-start; width: 83px; height: 1px; padding-top: 302px; margin-left: 11px;">
            <xhtml:div
               data-drawio-colors="color: rgb(0, 0, 0); "
               style="box-sizing: border-box; font-size: 0px; text-align: left;">
              <xhtml:div
                 style="display: inline-block; font-size: 12px; font-family: Open Sans; color: rgb(0, 0, 0); line-height: 1.2; pointer-events: all; white-space: normal; overflow-wrap: normal;">
                                At Customer's
                            </xhtml:div>
            </xhtml:div>
          </xhtml:div>
        </foreignObject>
        <text
           x="11"
           y="306"
           fill="#000000"
           font-family="'Open Sans'"
           font-size="12px"
           id="text112">At Customer's</text>
      </switch>
    </g>
    <text
       x="-44.566639"
       y="61.793201"
       fill="#000000"
       font-family="'Open Sans'"
       font-size="12px"
       id="text968"
       transform="rotate(-90)"><tspan
         sodipodi:role="line"
         id="tspan1082"
         x="-44.566639"
         y="61.793201"
         style="font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;font-family:'Open Sans', sans-serif;-inkscape-font-specification:'sans-serif Bold';text-align:center;text-anchor:middle">Order Status</tspan></text>
    <text
       x="-208.72852"
       y="61.48584"
       fill="#000000"
       font-family="'Open Sans'"
       font-size="12px"
       id="text1078"
       transform="rotate(-90)"><tspan
         sodipodi:role="line"
         id="tspan1149"
         x="-208.72852"
         y="61.48584"
         style="font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;font-family:'Open Sans', sans-serif;-inkscape-font-specification:'sans-serif Bold';text-align:center;text-anchor:middle">Cartridge Status</tspan></text>
  </g>
  <switch
     id="switch126"
     transform="translate(-48.868652,-1.8183594)">
    <g
       requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"
       id="g120" />
    <a
       transform="translate(0,-5)"
       xlink:href="https://www.diagrams.net/doc/faq/svg-export-text-problems"
       target="_blank"
       id="a124">
      <text
         text-anchor="middle"
         font-size="10px"
         x="50%"
         y="100%"
         id="text122">Text is not SVG - cannot display</text>
    </a>
  </switch>
</svg>

`;