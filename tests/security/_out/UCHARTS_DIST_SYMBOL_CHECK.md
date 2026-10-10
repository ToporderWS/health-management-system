=== 1. 语法校验（node --check） ===
  .js 文件数 = 23
  语法失败文件数 = 0

=== 2. common_vendor 符号完整性 ===
  vendor.js 导出符号数 = 21
  vendor.js 字节数 = 351754
  业务代码引用 common_vendor.X 去重后 = 21
  未定义的引用 = 0

=== 3. 各模块导出计数 ===
  api/index.js           exports=api
  common/auth.js         exports=clearAuth,ensureLogin,getToken,getUserInfo,isLogin,setAuth,setToken,setUserInfo
  common/config.js       exports=API_BASE_URL,SLEEP_QUALITY_OPTIONS,SPORT_STATUS_TEXT,SPORT_TYPES,resolveFileUrl
  common/image.js        exports=imgSrc
  common/request.js      exports=get,post,upload

=== 4. 页面/组件文件齐备 ===
  页面目录数 = 15
  缺失必需文件 = 0

DIST_SYMBOL_CHECK = PASS