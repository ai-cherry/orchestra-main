import{r as y}from"./vendor-CDaM45aE.js";var _={exports:{}},f={};/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var m=y,x=Symbol.for("react.element"),E=Symbol.for("react.fragment"),v=Object.prototype.hasOwnProperty,w=m.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,O={key:!0,ref:!0,__self:!0,__source:!0};function a(u,e,n){var r,s={},t=null,o=null;n!==void 0&&(t=""+n),e.key!==void 0&&(t=""+e.key),e.ref!==void 0&&(o=e.ref);for(r in e)v.call(e,r)&&!O.hasOwnProperty(r)&&(s[r]=e[r]);if(u&&u.defaultProps)for(r in e=u.defaultProps,e)s[r]===void 0&&(s[r]=e[r]);return{$$typeof:x,type:u,key:t,ref:o,props:s,_owner:w.current}}f.Fragment=E;f.jsx=a;f.jsxs=a;_.exports=f;var S=_.exports;function h(u,e,n,r){function s(t){return t instanceof n?t:new n(function(o){o(t)})}return new(n||(n=Promise))(function(t,o){function d(p){try{i(r.next(p))}catch(c){o(c)}}function l(p){try{i(r.throw(p))}catch(c){o(c)}}function i(p){p.done?t(p.value):s(p.value).then(d,l)}i((r=r.apply(u,e||[])).next())})}export{h as _,S as j};
