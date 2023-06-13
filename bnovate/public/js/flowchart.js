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
      'In Storage': '#in-storage',
      'Refill Pending': '#pending-fill',
      'Filling': '#filling',
      'Ready to Ship': '#ready-to-ship',
      'Shipped': '#shipped',
      'Awaiting Return': '#awaiting-return'
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
   height="319"
   viewBox="-0.5 -0.5 594.59198 319.00001"
   id="svg128"
   sodipodi:docname="flowchart4.svg"
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
     inkscape:zoom="1.8305599"
     inkscape:cx="245.00701"
     inkscape:cy="284.0661"
     inkscape:window-width="2560"
     inkscape:window-height="1387"
     inkscape:window-x="2992"
     inkscape:window-y="-8"
     inkscape:window-maximized="1"
     inkscape:current-layer="g118"
     showguides="true">
    <sodipodi:guide
       position="15.25366,128.83771"
       orientation="1,0"
       id="guide870"
       inkscape:locked="false" />
    <sodipodi:guide
       position="9.4245488,262.50288"
       orientation="1,0"
       id="guide331"
       inkscape:locked="false" />
    <sodipodi:guide
       position="246.91899,290.18369"
       orientation="0,-1"
       id="guide1208"
       inkscape:locked="false" />
    <sodipodi:guide
       position="573.86815,92.566549"
       orientation="1,0"
       id="guide2803"
       inkscape:locked="false" />
    <sodipodi:guide
       position="498.48137,158.93969"
       orientation="0,-1"
       id="guide2805"
       inkscape:locked="false" />
    <sodipodi:guide
       position="88.224375,273.93183"
       orientation="1,0"
       id="guide2809"
       inkscape:locked="false" />
  </sodipodi:namedview>
  <defs
     id="defs2">
    <linearGradient
       inkscape:collect="always"
       id="linearGradient3958">
      <stop
         style="stop-color:#62ff00;stop-opacity:1;"
         offset="0"
         id="stop3954" />
      <stop
         style="stop-color:#62ff00;stop-opacity:0;"
         offset="1"
         id="stop3956" />
    </linearGradient>
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3960"
       x1="-155.00352"
       y1="57.293201"
       x2="-79.780861"
       y2="57.293201"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3962"
       x1="-370.7168"
       y1="58.368652"
       x2="-274.5"
       y2="58.368652"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3964"
       x1="11"
       y1="101.5"
       x2="72.628906"
       y2="101.5"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3966"
       x1="11"
       y1="301.71387"
       x2="88.677734"
       y2="301.71387"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3970"
       x1="283.19141"
       y1="167.88281"
       x2="344.95508"
       y2="167.88281"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3972"
       x1="419.0791"
       y1="167.88281"
       x2="449.85254"
       y2="167.88281"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3974"
       x1="517.06836"
       y1="167.88574"
       x2="591.43555"
       y2="167.88574"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3976"
       x1="420.82324"
       y1="253.87334"
       x2="468.34863"
       y2="253.87334"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3978"
       x1="414.44238"
       y1="254"
       x2="473.5166"
       y2="254"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3980"
       x1="69.996094"
       y1="6.7753906"
       x2="98.548828"
       y2="6.7753906"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3982"
       x1="165.3418"
       y1="7.8769531"
       x2="222.79883"
       y2="7.8769531"
       gradientUnits="userSpaceOnUse" />
    <linearGradient
       inkscape:collect="always"
       xlink:href="#linearGradient3958"
       id="linearGradient3984"
       x1="285.08398"
       y1="6.4677734"
       x2="342.61719"
       y2="6.4677734"
       gradientUnits="userSpaceOnUse" />
  </defs>
  <g
     id="g118"
     transform="translate(-48.868652,-1.8183594)">
    <rect
       x="85.563835"
       y="95.111862"
       width="557.39685"
       height="105.75093"
       fill="#fff3e6"
       stroke="none"
       pointer-events="all"
       id="rect4"
       style="stroke-width:0.910572" />
    <rect
       x="85.563835"
       y="207"
       width="557.39685"
       height="105.75093"
       fill="#e0efff"
       stroke="none"
       pointer-events="all"
       id="rect6"
       style="stroke-width:0.910598" />
    <path
       d="M 207.19496,147 H 333.58632"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path8"
       style="stroke-width:1" />
    <path
       d="m 332.723,147.04628 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path10" />
    <circle
       id="in-storage"
       class="node"
       cx="198"
       cy="147"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       r="10" />
    <g
       transform="translate(3.5,-0.5)"
       id="g17"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="194.22754"
         y="170.88281"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text13"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1"><tspan
           sodipodi:role="line"
           id="tspan1657"
           x="194.22754"
           y="170.88281"
           style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">In Storage</tspan></text>
    </g>
    <path
       d="m 426.37949,147 h 46.815"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path19"
       style="stroke-width:0.999997" />
    <path
       d="m 477.67568,147 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path21" />
    <circle
       id="pending-fill"
       class="node"
       cx="343.58633"
       cy="147"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       r="10" />
    <g
       transform="translate(29.013088,-0.5)"
       id="g28"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="314"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text24"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Pending Fill</text>
    </g>
    <circle
       cx="416.37949"
       cy="147"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="filling"
       class="node"
       r="10" />
    <g
       transform="translate(-18.086334,-0.5)"
       id="g40"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="434"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text36"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Filling</text>
    </g>
    <path
       d="m 499.17267,147 112.78189,-0.01 c 6.30215,-5.4e-4 9.45322,3.33388 9.45322,10.00163 v 100.01624 c 0,6.66775 -3.15107,9.99668 -9.45322,10.00163 l -39.98874,0.0314"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path42"
       style="stroke-width:0.972;stroke-dasharray:none"
       sodipodi:nodetypes="cssssc" />
    <path
       d="m 572.68564,267.04111 7,-3.5 -1.75,3.5 1.75,3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path44" />
    <circle
       cx="489.17267"
       cy="147"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="ready-to-ship"
       class="node"
       r="10" />
    <g
       transform="translate(-65.079285,-0.5)"
       id="g52"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="554"
         y="171"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text48"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Ready to Ship</text>
    </g>
    <path
       d="m 260.79315,267.04111 -115.25874,-0.0235 c -6.01662,-10e-4 -9.02493,-3.33431 -9.02493,-10.00293 V 156.98534 c 0,-6.66862 3.00831,-10.00293 9.02493,-10.00293 h 38.4007"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path54"
       style="stroke-width:0.950136"
       sodipodi:nodetypes="cssssc" />
    <path
       d="m 186.88,147 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path56" />
    <circle
       cx="561.96582"
       cy="267.04111"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="shipped"
       class="node"
       r="10" />
    <g
       transform="translate(117.98633,-17.26864)"
       id="g64"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="444"
         y="251"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text60"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1"><tspan
           sodipodi:role="line"
           id="tspan1663"
           x="444"
           y="251"
           style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Shipped to</tspan><tspan
           sodipodi:role="line"
           id="tspan1665"
           x="444"
           y="266"
           style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Customer</tspan></text>
    </g>
    <path
       d="m 343.58633,37 v 93.63"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path66"
       style="stroke-dasharray:4, 2;stroke-dashoffset:0" />
    <path
       d="m 343.58633,135.88 -3.5,-7 3.5,1.75 3.5,-1.75 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path68" />
    <circle
       cx="343.58633"
       cy="43"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="confirmed"
       class="node"
       r="10" />
    <g
       transform="translate(29.735748,14.97469)"
       id="g76"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="314"
         y="11"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text72"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Confirmed</text>
    </g>
    <path
       d="m 281.29315,43.5 h 45.11044"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path78"
       style="stroke-width:1" />
    <path
       d="m 331.90358,43.5 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path80" />
    <circle
       cx="270.79315"
       cy="43"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="requested"
       class="node"
       r="10" />
    <g
       transform="translate(76.722839,14.91024)"
       id="g88"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="194"
         y="11"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text84"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Requested</text>
    </g>
    <path
       d="m 208.00001,43.57936 h 45.92512"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path90"
       style="stroke-width:0.999999" />
    <path
       d="m 259.17512,43.57936 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path92" />
    <circle
       cx="197.57324"
       cy="42.5"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="none"
       class="node"
       r="10" />
    <g
       transform="translate(113.30078,14.66708)"
       id="g100"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="84"
         y="11"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text96"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">None</text>
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
       transform="rotate(-90,99.43402,90.36776)"
       id="g108"
       style="fill:#505050;fill-opacity:1;stroke:none;stroke-opacity:1">
      <switch
         id="switch106"
         style="fill:#505050;fill-opacity:1;stroke:none;stroke-opacity:1">
        <foreignObject
           pointer-events="none"
           width="100%"
           height="100%"
           requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"
           style="overflow:visible;text-align:left;fill-opacity:1;fill:url(#linearGradient3964)">
          <xhtml:div
             style="display:flex;align-items:unsafe center;justify-content:unsafe flex-start;width:83px;height:1px;padding-top:102px;margin-left:11px;fill-opacity:1;fill:url(#linearGradient3964)">
            <xhtml:div
               data-drawio-colors="color: rgb(0, 0, 0); "
               style="box-sizing:border-box;font-size:0px;text-align:left;fill-opacity:1;fill:url(#linearGradient3964)">
              <xhtml:div
                 style="display:inline-block;font-size:12px;font-family:Open Sans;color:rgb(0, 0, 0);line-height:1.2;pointer-events:all;white-space:normal;overflow-wrap:normal;fill-opacity:1;fill:url(#linearGradient3964)">
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
           id="text104"
           style="fill:#505050;fill-opacity:1;stroke:none;stroke-opacity:1">At bNovate</text>
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
       transform="rotate(-90,59.7331,250.52035)"
       id="g116"
       style="fill:#505050;fill-opacity:1;stroke:none;stroke-opacity:1">
      <switch
         id="switch114"
         style="fill:#505050;fill-opacity:1;stroke:none;stroke-opacity:1">
        <foreignObject
           pointer-events="none"
           width="100%"
           height="100%"
           requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"
           style="overflow:visible;text-align:left;fill-opacity:1;fill:url(#linearGradient3966)">
          <xhtml:div
             style="display:flex;align-items:unsafe center;justify-content:unsafe flex-start;width:83px;height:1px;padding-top:302px;margin-left:11px;fill-opacity:1;fill:url(#linearGradient3966)">
            <xhtml:div
               data-drawio-colors="color: rgb(0, 0, 0); "
               style="box-sizing:border-box;font-size:0px;text-align:left;fill-opacity:1;fill:url(#linearGradient3966)">
              <xhtml:div
                 style="display:inline-block;font-size:12px;font-family:Open Sans;color:rgb(0, 0, 0);line-height:1.2;pointer-events:all;white-space:normal;overflow-wrap:normal;fill-opacity:1;fill:url(#linearGradient3966)">
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
           id="text112"
           style="fill:#505050;fill-opacity:1;stroke:none;stroke-opacity:1">At Customer's</text>
      </switch>
    </g>
    <text
       x="-42.620117"
       y="67.793198"
       fill="#000000"
       font-family="'Open Sans'"
       font-size="12px"
       id="text968"
       transform="rotate(-90)"
       style="fill:#313131;fill-opacity:1;stroke:none;stroke-opacity:1"><tspan
         sodipodi:role="line"
         id="tspan1082"
         x="-42.620117"
         y="67.793198"
         style="font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;font-family:'Open Sans', sans-serif;-inkscape-font-specification:'sans-serif Bold';text-align:center;text-anchor:middle;fill:#313131;fill-opacity:1;stroke:none;stroke-opacity:1">Order Status</tspan></text>
    <text
       x="-204.72852"
       y="67.48584"
       fill="#000000"
       font-family="'Open Sans'"
       font-size="12px"
       id="text1078"
       transform="rotate(-90)"
       style="fill:#313131;fill-opacity:1;stroke:none;stroke-opacity:1"><tspan
         sodipodi:role="line"
         id="tspan1149"
         x="-204.72852"
         y="67.48584"
         style="font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;font-family:'Open Sans', sans-serif;-inkscape-font-specification:'sans-serif Bold';text-align:center;text-anchor:middle;fill:#313131;fill-opacity:1;stroke:none;stroke-opacity:1">Cartridge Status</tspan></text>
    <path
       d="m 334.91223,140.25358 -6.69253,-4.0571 3.89414,-0.38492 2.02855,-3.34626 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path1210" />
    <path
       d="m 275.8611,51.38245 59.64707,89.72321"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path1212"
       sodipodi:nodetypes="cc"
       style="stroke-dasharray:4, 2;stroke-dashoffset:0" />
    <circle
       cx="270.79315"
       cy="267.04111"
       fill="#ffffff"
       stroke="#000000"
       pointer-events="all"
       id="awaiting-return"
       class="node"
       r="10" />
    <g
       transform="translate(-173.79279,-17.14198)"
       id="g1380"
       style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">
      <text
         x="444.70605"
         y="250.72685"
         fill="#000000"
         font-family="'Open Sans'"
         font-size="12px"
         text-anchor="middle"
         id="text1378"
         style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1"><tspan
           sodipodi:role="line"
           id="tspan1659"
           x="444.70605"
           y="250.72685"
           style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Awaiting</tspan><tspan
           sodipodi:role="line"
           id="tspan1661"
           x="444.70605"
           y="265.72687"
           style="fill:#272727;fill-opacity:1;stroke:none;stroke-opacity:1">Return</tspan></text>
    </g>
    <path
       d="M 551.96585,267.01619 H 282.07561"
       fill="none"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="stroke"
       id="path1484"
       style="stroke-width:1" />
    <path
       d="m 282.02244,267.04111 7.46726,3.5 -1.86681,-3.5 1.86681,-3.5 z"
       fill="#000000"
       stroke="#000000"
       stroke-miterlimit="10"
       pointer-events="all"
       id="path1486"
       style="stroke-width:0.999999" />
    <g
       id="g1693"
       transform="translate(72.770744,-118)">
      <path
         d="m 281.11658,265 h 46.15404"
         fill="none"
         stroke="#000000"
         stroke-miterlimit="10"
         pointer-events="stroke"
         id="path1689"
         style="stroke-width:1" />
      <path
         d="m 332.16731,265 -7,3.5 1.75,-3.5 -1.75,-3.5 z"
         fill="#000000"
         stroke="#000000"
         stroke-miterlimit="10"
         pointer-events="all"
         id="path1691" />
    </g>
    <g
       transform="translate(236.76503,331.13718)"
       id="g1807"
       style="fill:#505050;fill-opacity:1" />
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