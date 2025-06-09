from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`,G=b`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`,B=b`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`,V=m("div")`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||"#ff4b4b"};
  position: relative;
  transform: rotate(45deg);

  animation: ${H} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${G} 0.15s ease-out forwards;
    animation-delay: 150ms;
    position: absolute;
    border-radius: 3px;
    opacity: 0;
    background: ${e=>e.secondary||"#fff"};
    bottom: 9px;
    left: 4px;
    height: 2px;
    width: 12px;
  }

  &:before {
    animation: ${B} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`,$=b`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`,z=m("div")`
  width: 12px;
  height: 12px;
  box-sizing: border-box;
  border: 2px solid;
  border-radius: 100%;
  border-color: ${e=>e.secondary||"#e0e0e0"};
  border-right-color: ${e=>e.primary||"#616161"};
  animation: ${$} 1s linear infinite;
`,X=b`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(45deg);
	opacity: 1;
}`,W=b`
0% {
	height: 0;
	width: 0;
	opacity: 0;
}
40% {
  height: 0;
	width: 6px;
	opacity: 1;
}
100% {
  opacity: 1;
  height: 10px;
}`,K=m("div")`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||"#61d345"};
  position: relative;
  transform: rotate(45deg);

  animation: ${X} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;
  &:after {
    content: '';
    box-sizing: border-box;
    animation: ${W} 0.2s ease-out forwards;
    opacity: 0;
    animation-delay: 200ms;
    position: absolute;
    border-right: 2px solid;
    border-bottom: 2px solid;
    border-color: ${e=>e.secondary||"#fff"};
    bottom: 6px;
    left: 6px;
    height: 10px;
    width: 6px;
  }
`,Y=m("div")`
  position: absolute;
`,q=m("div")`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`,J=b`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`,Q=m("div")`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${J} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`,Z=({toast:e})=>{let{icon:t,type:r,iconTheme:n}=e;return void 0!==t?"string"==typeof t?a.createElement(Q,null,t):t:"blank"===r?null:a.createElement(q,null,a.createElement(z,{...n}),"loading"!==r&&a.createElement(Y,null,"error"===r?a.createElement(V,{...n}):a.createElement(K,{...n})))},ee=e=>`
0% {transform: translate3d(0,${-200*e}%,0) scale(.6); opacity:.5;}
100% {transform: translate3d(0,0,0) scale(1); opacity:1;}
`,et=e=>`
0% {transform: translate3d(0,0,-1px) scale(1); opacity:1;}
100% {transform: translate3d(0,${-150*e}%,-1px) scale(.6); opacity:0;}
`,er=m("div")`
  display: flex;
  align-items: center;
  background: #fff;
  color: #363636;
  line-height: 1.3;
  will-change: transform;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1), 0 3px 3px rgba(0, 0, 0, 0.05);
  max-width: 350px;
  pointer-events: auto;
  padding: 8px 10px;
  border-radius: 8px;
`,en=m("div")`
  display: flex;
  justify-content: center;
  margin: 4px 10px;
  color: inherit;
  flex: 1 1 auto;
  white-space: pre-line;
`,ea=(e,t)=>{let r=e.includes("top")?1:-1,[n,a]=O()?["0%{opacity:0;} 100%{opacity:1;}","0%{opacity:1;} 100%{opacity:0;}"]:[ee(r),et(r)];return{animation:t?`${b(n)} 0.35s cubic-bezier(.21,1.02,.73,1) forwards`:`${b(a)} 0.4s forwards cubic-bezier(.06,.71,.55,1)`}},eo=a.memo(({toast:e,position:t,style:r,children:n})=>{let o=e.height?ea(e.position||t||"top-center",e.visible):{opacity:0},i=a.createElement(Z,{toast:e}),l=a.createElement(en,{...e.ariaProps},R(e.message,e));return a.createElement(er,{className:e.className,style:{...o,...r,...e.style}},"function"==typeof n?n({icon:i,message:l}):a.createElement(a.Fragment,null,i,l))});n=a.createElement,c.p=void 0,y=n,_=void 0,v=void 0;var ei=({id:e,className:t,style:r,onHeightUpdate:n,children:o})=>{let i=a.useCallback(t=>{if(t){let r=()=>{n(e,t.getBoundingClientRect().height)};r(),new MutationObserver(r).observe(t,{subtree:!0,childList:!0,characterData:!0})}},[e,n]);return a.createElement("div",{ref:i,className:t,style:r},o)},el=(e,t)=>{let r=e.includes("top"),n=e.includes("center")?{justifyContent:"center"}:e.includes("right")?{justifyContent:"flex-end"}:{};return{left:0,right:0,display:"flex",position:"absolute",transition:O()?void 0:"all 230ms cubic-bezier(.21,1.02,.73,1)",transform:`translateY(${t*(r?1:-1)}px)`,...r?{top:0}:{bottom:0},...n}},eu=g`
  z-index: 9999;
  > * {
    pointer-events: auto;
  }
`,es=({reverseOrder:e,position:t="top-center",toastOptions:r,gutter:n,children:o,containerStyle:i,containerClassName:l})=>{let{toasts:u,handlers:s}=k(r);return a.createElement("div",{id:"_rht_toaster",style:{position:"fixed",zIndex:9999,top:16,left:16,right:16,bottom:16,pointerEvents:"none",...i},className:l,onMouseEnter:s.startPause,onMouseLeave:s.endPause},u.map(r=>{let i=r.position||t,l=el(i,s.calculateOffset(r,{reverseOrder:e,gutter:n,defaultPosition:t}));return a.createElement(ei,{id:r.id,key:r.id,onHeightUpdate:s.updateHeight,className:r.visible?eu:"",style:l},"custom"===r.type?R(r.message,r):o?o(r):a.createElement(eo,{toast:r,position:i}))}))}},3370:(e,t,r)=>{"use strict";function n(e){return e&&e.__esModule?e:{default:e}}r.r(t),r.d(t,{_:()=>n,_interop_require_default:()=>n})},9125:(e,t,r)=>{"use strict";r.d(t,{x7:()=>a});var n=r(8570);(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#CheckmarkIcon`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#ErrorIcon`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#LoaderIcon`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#ToastBar`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#ToastIcon`);let a=(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#Toaster`);(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#default`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#resolveValue`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#toast`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#useToaster`),(0,n.createProxy)(String.raw`/home/ubuntu/orchestra-main-repo/admin-interface/node_modules/react-hot-toast/dist/index.mjs#useToasterStore`)}};