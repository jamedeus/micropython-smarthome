(()=>{"use strict";var e={n:t=>{var n=t&&t.__esModule?()=>t.default:()=>t;return e.d(n,{a:n}),n},d:(t,n)=>{for(var r in n)e.o(n,r)&&!e.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:n[r]})},o:(e,t)=>Object.prototype.hasOwnProperty.call(e,t)};const t=React;var n=e.n(t);const r=ReactDOM;var a=e.n(r);const o=function(e){var t=e.children,r=e.label;return n().createElement("div",{className:"mb-2"},n().createElement("label",{className:"w-100"},n().createElement("b",null,r,":"),t))},l=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(o,{label:"Nickname"},n().createElement("input",{type:"text",className:"form-control nickname",placeholder:"",value:r,onChange:function(e){return a(t,e.target.value)},required:!0}))},c=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(o,{label:"IP"},n().createElement("input",{type:"text",className:"form-control ip-input validate",placeholder:"",value:r,pattern:"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",onChange:function(e){return a(t,e.target.value)},required:!0}))},u=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(o,{label:"URI"},n().createElement("input",{type:"text",className:"form-control validate",placeholder:"IP address or URL",value:r,pattern:"(?:(?:http|https):\\/\\/)?(?:\\S+(?::\\S*)?@)?(?:(?:[0-9]{1,3}\\.){3}[0-9]{1,3})(?::\\d{1,5})?|(?:(?:http|https):\\/\\/)?[a-zA-Z0-9.]+(?:-[a-zA-Z0-9]+)*(?:\\.[a-zA-Z]{2,6})+(?:\\/\\S*)?",onChange:function(e){return a(t,e.target.value)},required:!0}))},i=function(e){e.id;var t=e.on_path,r=e.off_path,a=e.onChange;return n().createElement(n().Fragment,null,n().createElement(o,{label:"On path"},n().createElement("input",{type:"text",className:"form-control validate",placeholder:"Appended to URI for on action",value:t,onChange:function(e){return a(e.target.value)},required:!0})),n().createElement(o,{label:"Off path"},n().createElement("input",{type:"text",className:"form-control validate",placeholder:"Appended to URI for off action",value:r,onChange:function(e){return a(e.target.value)},required:!0})))},s=function(e){e.id;var t=e.mode,r=e.units,a=e.tolerance,l=e.onChange;return n().createElement(n().Fragment,null,n().createElement(o,{label:"Mode"},n().createElement("select",{className:"form-select",value:t,onChange:function(e){return l(e.target.value)},required:!0},n().createElement("option",{value:"cool"},"Cool"),n().createElement("option",{value:"heat"},"Heat"))),n().createElement(o,{label:"Units"},n().createElement("select",{className:"form-select",value:r,required:!0},n().createElement("option",{value:"fahrenheit"},"Fahrenheit"),n().createElement("option",{value:"celsius"},"Celsius"),n().createElement("option",{value:"kelvin"},"Kelvin"))),n().createElement(o,{label:"Tolerance"},n().createElement("input",{type:"text",className:"form-control thermostat",placeholder:"",value:a,onChange:function(e){return l(e.target.value)},required:!0})))},m=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(o,{label:"Pin"},n().createElement("select",{className:"form-select pin-select",value:r,autoComplete:"off",onChange:function(e){return a(t,e.target.value)},required:!0},n().createElement("option",null,"Select pin"),n().createElement("option",{value:"4"},"4"),n().createElement("option",{value:"5"},"5"),n().createElement("option",{value:"13"},"13"),n().createElement("option",{value:"14"},"14"),n().createElement("option",{value:"15"},"15"),n().createElement("option",{value:"16"},"16"),n().createElement("option",{value:"17"},"17"),n().createElement("option",{value:"18"},"18"),n().createElement("option",{value:"19"},"19"),n().createElement("option",{value:"21"},"21"),n().createElement("option",{value:"22"},"22"),n().createElement("option",{value:"23"},"23"),n().createElement("option",{value:"25"},"25"),n().createElement("option",{value:"26"},"26"),n().createElement("option",{value:"27"},"27"),n().createElement("option",{value:"32"},"32"),n().createElement("option",{value:"33"},"33"),n().createElement("option",{value:"34"},"34"),n().createElement("option",{value:"35"},"35"),n().createElement("option",{value:"36"},"36"),n().createElement("option",{value:"39"},"39")))},p=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(o,{label:"Pin"},n().createElement("select",{className:"form-select pin-select",value:r,autoComplete:"off",onChange:function(e){return a(t,e.target.value)},required:!0},n().createElement("option",null,"Select pin"),n().createElement("option",{value:"4"},"4"),n().createElement("option",{value:"13"},"13"),n().createElement("option",{value:"16"},"16"),n().createElement("option",{value:"17"},"17"),n().createElement("option",{value:"18"},"18"),n().createElement("option",{value:"19"},"19"),n().createElement("option",{value:"21"},"21"),n().createElement("option",{value:"22"},"22"),n().createElement("option",{value:"23"},"23"),n().createElement("option",{value:"25"},"25"),n().createElement("option",{value:"26"},"26"),n().createElement("option",{value:"27"},"27"),n().createElement("option",{value:"32"},"32"),n().createElement("option",{value:"33"},"33")))},f=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement("div",{className:"mb-2"},n().createElement("label",{className:"w-100"},n().createElement("b",null,"Default Rule:"),n().createElement("select",{className:"form-select",value:r,autoComplete:"off",onChange:function(e){return a(t,e.target.value)},required:!0},n().createElement("option",{disabled:!0},"Select default rule"),n().createElement("option",{value:"enabled"},"Enabled"),n().createElement("option",{value:"disabled"},"Disabled"))))},d=function(e){var t=e.id,r=e.value,a=e.metadata,l=e.onChange;return n().createElement(o,{label:"Default Rule"},n().createElement("div",{className:"d-flex flex-row align-items-center my-2"},n().createElement("button",{className:"btn btn-sm me-1","data-direction":"down","data-stepsize":"0.5"},n().createElement("i",{className:"bi-dash-lg"})),n().createElement("input",{type:"range",className:"mx-auto",min:a.rule_limits[0],max:a.rule_limits[1],"data-displaymin":a.rule_limits[0],"data-displaymax":a.rule_limits[1],"data-displaytype":"float",step:"0.5",value:r,onChange:function(e){return l(t,e.target.value)},autoComplete:"off"}),n().createElement("button",{className:"btn btn-sm ms-1","data-direction":"up","data-stepsize":"0.5"},n().createElement("i",{className:"bi-plus-lg"}))))},v=function(e){var t=e.id,r=e.value,a=e.min,l=e.max,c=e.metadata,u=e.onChange;return n().createElement(n().Fragment,null,n().createElement(o,{label:"Default Rule"},n().createElement("div",{className:"d-flex flex-row align-items-center my-2"},n().createElement("button",{className:"btn btn-sm me-1","data-direction":"down","data-stepsize":"1"},n().createElement("i",{className:"bi-dash-lg"})),n().createElement("input",{type:"range",className:"mx-auto",min:c.rule_limits[0],max:c.rule_limits[1],"data-displaymin":"1","data-displaymax":"100","data-displaytype":"int",step:"1",value:r,onChange:function(e){return u(t,e.target.value)},autoComplete:"off"}),n().createElement("button",{className:"btn btn-sm ms-1","data-direction":"up","data-stepsize":"1"},n().createElement("i",{className:"bi-plus-lg"})))),n().createElement("div",{className:"mt-3 text-center"},n().createElement("a",{className:"text-decoration-none text-dim","data-bs-toggle":"collapse",href:"#{id}-advanced_settings",role:"button","aria-expanded":"false","aria-controls":"{id}-advanced_settings"},"Advanced")),n().createElement("div",{id:"{id}-advanced_settings",className:"collapse"},n().createElement(o,{label:"Min brightness"},n().createElement("input",{type:"text",className:"form-control rule-limits",value:a,"data-min":c.rule_limits[0],"data-max":c.rule_limits[1],onChange:function(e){return u("min_rule",e.target.value)},required:!0})),n().createElement(o,{label:"Max brightness"},n().createElement("input",{type:"text",className:"form-control rule-limits",value:l,"data-min":c.rule_limits[0],"data-max":c.rule_limits[1],onChange:function(e){return u("max_rule",e.target.value)},required:!0}))))},y=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(o,{label:"Default Rule"},n().createElement("select",{className:"form-select",value:r,autoComplete:"off",onChange:function(e){return a(t,e.target.value)},required:!0},n().createElement("option",{disabled:!0},"Select default rule"),n().createElement("option",{value:"on"},"On"),n().createElement("option",{value:"off"},"Off")))},b=function(e){var t=e.id,r=e.value,a=e.onChange;return n().createElement(n().Fragment,null,n().createElement("div",{className:"mb-2 text-center"},n().createElement("button",{id:"{id}-default_rule-button",className:"btn btn-secondary mt-3 {id}",type:"button"},"Set rule")),n().createElement("div",{className:"d-none"},n().createElement("input",{type:"text",id:"{id}-default_rule",value:r,onChange:function(e){return a(t,e.target.value)},required:!0})))};function h(e){return h="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},h(e)}function E(e,t){(null==t||t>e.length)&&(t=e.length);for(var n=0,r=new Array(t);n<t;n++)r[n]=e[n];return r}function g(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,w(r.key),r)}}function _(e,t){return _=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(e,t){return e.__proto__=t,e},_(e,t)}function C(e){if(void 0===e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return e}function O(e){return O=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(e){return e.__proto__||Object.getPrototypeOf(e)},O(e)}function N(e,t,n){return(t=w(t))in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function w(e){var t=function(e,t){if("object"!==h(e)||null===e)return e;var n=e[Symbol.toPrimitive];if(void 0!==n){var r=n.call(e,"string");if("object"!==h(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(e)}(e);return"symbol"===h(t)?t:String(t)}const j=function(e){!function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),Object.defineProperty(e,"prototype",{writable:!1}),t&&_(e,t)}(j,e);var t,r,a,o,w=(a=j,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(e){return!1}}(),function(){var e,t=O(a);if(o){var n=O(this).constructor;e=Reflect.construct(t,arguments,n)}else e=t.apply(this,arguments);return function(e,t){if(t&&("object"===h(t)||"function"==typeof t))return t;if(void 0!==t)throw new TypeError("Derived constructors may only return object or undefined");return C(e)}(this,e)});function j(){var e;!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,j);for(var t=arguments.length,r=new Array(t),a=0;a<t;a++)r[a]=arguments[a];return N(C(e=w.call.apply(w,[this].concat(r))),"renderInputs",(function(t,r,a){var o=[];return void 0!==t.nickname&&o.push(n().createElement(l,{key:"nickname",id:"nickname",value:t.nickname,onChange:e.props.onInputChange})),void 0!==t.pin&&(void 0===t.targets?o.push(n().createElement(p,{key:"pin",id:"pin",value:t.pin,onChange:e.props.onInputChange})):o.push(n().createElement(m,{key:"pin",id:"pin",value:t.pin,onChange:e.props.onInputChange}))),void 0!==t.ip&&o.push(n().createElement(c,{key:"ip",id:"ip",value:t.ip,onChange:e.props.onInputChange})),void 0!==t.uri&&o.push(n().createElement(u,{key:"uri",id:"uri",value:t.uri,onChange:e.props.onInputChange})),void 0!==t.on_path&&void 0!==t.off_path&&o.push(n().createElement(i,{key:"on_off_path",id:"on_off_path",on_path:t.on_path,off_path:t.off_path,onChange:e.props.onInputChange})),o.push(e.renderRuleInput(t,r,a)),void 0!==t.mode&&void 0!==t.units&&o.push(n().createElement(s,{key:"thermostat",id:"thermostat",mode:t.mode,units:t.units,tolerance:t.tolerance,onChange:e.props.onInputChange})),o})),N(C(e),"renderRuleInput",(function(t,r,a){if(void 0===t._type)return null;var o=a["".concat(r,"s")][t._type];switch(o.rule_prompt){case"standard":return n().createElement(f,{key:"default_rule",id:"default_rule",value:t.default_rule,onChange:e.props.onInputChange});case"on_off":return n().createElement(y,{key:"default_rule",id:"default_rule",value:t.default_rule,onChange:e.props.onInputChange});case"float_range":return n().createElement(d,{key:"default_rule",id:"default_rule",value:t.default_rule,metadata:o,onChange:e.props.onInputChange});case"int_or_fade":return n().createElement(v,{key:"default_rule",id:"default_rule",value:t.default_rule,min:t.min_rule,max:t.max_rule,metadata:o,onChange:e.props.onInputChange});case"api_target":return n().createElement(b,{key:"default_rule",id:"default_rule",value:t.default_rule,onChange:e.props.onInputChange});default:return null}})),e}return t=j,(r=[{key:"render",value:function(){var e=this,t=this.props,r=t.id,a=t.category,o=t.config,l=metadata;return console.log(o),n().createElement("div",{className:"fade-in mb-4"},n().createElement("div",{className:"card"},n().createElement("div",{className:"card-body"},n().createElement("div",{className:"d-flex justify-content-between"},n().createElement("button",{className:"btn ps-2",style:{visibility:"hidden"}},n().createElement("i",{className:"bi-x-lg"})),n().createElement("h4",{className:"card-title mx-auto my-auto"},"".concat(r)),n().createElement("button",{className:"btn my-auto pe-2 delete",onClick:function(){return e.props.onDelete(r)}},n().createElement("i",{className:"bi-x-lg"}))),n().createElement("label",{className:"w-100"},n().createElement("b",null,"Type:"),n().createElement("select",{className:"form-select mt-2","data-param":"_type",required:!0,onChange:this.props.onTypeChange},n().createElement("option",{value:"clear"},"Select ",a," type"),Object.entries(l["".concat(a,"s")]).map((function(e){var t,r,a=(r=2,function(e){if(Array.isArray(e))return e}(t=e)||function(e,t){var n=null==e?null:"undefined"!=typeof Symbol&&e[Symbol.iterator]||e["@@iterator"];if(null!=n){var r,a,o,l,c=[],u=!0,i=!1;try{if(o=(n=n.call(e)).next,0===t){if(Object(n)!==n)return;u=!1}else for(;!(u=(r=o.call(n)).done)&&(c.push(r.value),c.length!==t);u=!0);}catch(e){i=!0,a=e}finally{try{if(!u&&null!=n.return&&(l=n.return(),Object(l)!==l))return}finally{if(i)throw a}}return c}}(t,r)||function(e,t){if(e){if("string"==typeof e)return E(e,t);var n=Object.prototype.toString.call(e).slice(8,-1);return"Object"===n&&e.constructor&&(n=e.constructor.name),"Map"===n||"Set"===n?Array.from(e):"Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?E(e,t):void 0}}(t,r)||function(){throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()),o=a[0],l=a[1];return n().createElement("option",{key:o,value:l.config_name},l.class_name)})))),n().createElement("div",{id:"".concat(r,"-params"),className:"card-body"},this.renderInputs(o,a,l)))))}}])&&g(t.prototype,r),Object.defineProperty(t,"prototype",{writable:!1}),j}(n().Component);function S(e){return S="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},S(e)}function x(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function I(e,t){return function(e){if(Array.isArray(e))return e}(e)||function(e,t){var n=null==e?null:"undefined"!=typeof Symbol&&e[Symbol.iterator]||e["@@iterator"];if(null!=n){var r,a,o,l,c=[],u=!0,i=!1;try{if(o=(n=n.call(e)).next,0===t){if(Object(n)!==n)return;u=!1}else for(;!(u=(r=o.call(n)).done)&&(c.push(r.value),c.length!==t);u=!0);}catch(e){i=!0,a=e}finally{try{if(!u&&null!=n.return&&(l=n.return(),Object(l)!==l))return}finally{if(i)throw a}}return c}}(e,t)||function(e,t){if(e){if("string"==typeof e)return P(e,t);var n=Object.prototype.toString.call(e).slice(8,-1);return"Object"===n&&e.constructor&&(n=e.constructor.name),"Map"===n||"Set"===n?Array.from(e):"Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?P(e,t):void 0}}(e,t)||function(){throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()}function P(e,t){(null==t||t>e.length)&&(t=e.length);for(var n=0,r=new Array(t);n<t;n++)r[n]=e[n];return r}function k(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,q(r.key),r)}}function R(e,t){return R=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(e,t){return e.__proto__=t,e},R(e,t)}function A(e){if(void 0===e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return e}function T(e){return T=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(e){return e.__proto__||Object.getPrototypeOf(e)},T(e)}function D(e,t,n){return(t=q(t))in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function q(e){var t=function(e,t){if("object"!==S(e)||null===e)return e;var n=e[Symbol.toPrimitive];if(void 0!==n){var r=n.call(e,"string");if("object"!==S(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(e)}(e);return"symbol"===S(t)?t:String(t)}const B=function(e){!function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),Object.defineProperty(e,"prototype",{writable:!1}),t&&R(e,t)}(c,e);var t,r,a,o,l=(a=c,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(e){return!1}}(),function(){var e,t=T(a);if(o){var n=T(this).constructor;e=Reflect.construct(t,arguments,n)}else e=t.apply(this,arguments);return function(e,t){if(t&&("object"===S(t)||"function"==typeof t))return t;if(void 0!==t)throw new TypeError("Derived constructors may only return object or undefined");return A(e)}(this,e)});function c(e){var t;return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,c),D(A(t=l.call(this,e)),"logState",(function(){console.log(t.state)})),D(A(t),"addInstance",(function(e){t.setState((function(t){t["num_".concat(e,"s")]+=1;var n=t["num_".concat(e,"s")];return t["".concat(e).concat(n)]={},t}))})),D(A(t),"deleteInstance",(function(e){t.setState((function(t){return delete t[e],e.startsWith("sensor")?t.num_sensors-=1:t.num_devices-=1,t}))})),D(A(t),"changeInstanceType",(function(e,n,r){t.setState((function(t){var a=metadata["".concat(n,"s")][r.target.value].config_template;return t[e]=a,t}))})),D(A(t),"handleInputChange",(function(e,n,r){console.log(n),t.setState((function(t){return t[e][n]=r,t}))})),D(A(t),"renderLayout",(function(){var e=Object.entries(t.state).filter((function(e){var t=I(e,2),n=t[0];return t[1],n.startsWith("device")})).map((function(e){var r=I(e,2),a=r[0],o=r[1];return n().createElement(j,{key:a,id:a,category:"device",config:o,onDelete:function(){return t.deleteInstance(a)},onInputChange:function(e,n){return t.handleInputChange(a,e,n)},onTypeChange:function(e){return t.changeInstanceType(a,"device",e)}})})),r=Object.entries(t.state).filter((function(e){var t=I(e,2),n=t[0];return t[1],n.startsWith("sensor")})).map((function(e){var r=I(e,2),a=r[0],o=r[1];return n().createElement(j,{key:a,id:a,category:"sensor",config:o,onDelete:function(){return t.deleteInstance(a)},onInputChange:function(e,n){return t.handleInputChange(a,e,n)},onTypeChange:function(e){return t.changeInstanceType(a,"sensor",e)}})}));return n().createElement(n().Fragment,null,n().createElement("h1",{className:"text-center pt-3 pb-4"},"TEST"),n().createElement("div",{id:"page1",className:"d-flex flex-column h-100"},n().createElement("div",{className:"row mt-3"},n().createElement("div",{id:"sensors",className:"col-sm"},n().createElement("h2",{className:"text-center"},"Add Sensors"),n().createElement("div",{id:"addSensorButton",className:"text-center position-relative"},n().createElement("button",{className:"btn-secondary btn mb-3",onClick:function(){return t.addInstance("sensor")}},"Add Sensor"),r)),n().createElement("div",{id:"devices",className:"col-sm"},n().createElement("h2",{className:"text-center"},"Add Devices"),n().createElement("div",{id:"addDeviceButton",className:"text-center position-relative"},n().createElement("button",{className:"btn-secondary btn mb-3",onClick:function(){return t.addInstance("device")}},"Add Device"),e)))),n().createElement("div",{className:"bottom"},n().createElement("button",{className:"log-button",onClick:function(){return t.logState()}},"Log State")))})),t.state={metadata:{},wifi:{},num_sensors:0,num_devices:0},t}return t=c,r=[{key:"componentDidMount",value:function(){var e=JSON.parse(document.getElementById("config").textContent);console.log(e),e&&this.setState(function(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?x(Object(n),!0).forEach((function(t){D(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):x(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}({},e))}},{key:"render",value:function(){return this.renderLayout()}}],r&&k(t.prototype,r),Object.defineProperty(t,"prototype",{writable:!1}),c}(n().Component);a().render(n().createElement(B,null),document.getElementById("root"))})();